#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import psutil
import subprocess
import os
import yaml
from threading import Thread
import srvdb
import requests as orig_requests
import time

from flask import Flask
from flask import request

from two1.commands.config import Config
from two1.wallet.two1_wallet import Wallet
from two1.bitserv.flask import Payment
from two1.bitrequests import BitTransferRequests

# set up bitrequest client for BitTransfer requests
wallet = Wallet()
username = Config().username
requests = BitTransferRequests(wallet, username)

app = Flask(__name__)
# app.debug = True

# setup wallet
wallet = Wallet()
payment = Payment(app, wallet)

# logging
logger = logging.getLogger('werkzeug')

# db handle
db = srvdb.SrvDb("./ping-aggregator.db")


@app.route('/manifest')
def manifest():
    """Provide the app manifest to the 21 crawler.
    """
    with open('./manifest.yaml', 'r') as f:
        manifest = yaml.load(f)
    return json.dumps(manifest)


def get_payment_amt(request):
    """
    Return the amount of the request based on the number of nodes.
    """
    print(request.data)
    user_input = json.loads(request.data.decode('UTF-8'))
    cost = 1000
    nodes = db.get_cheapest_nodes(user_input['nodes'])
    for node in nodes:
        cost = cost + node['price']

    return cost


@app.route('/', methods=['POST'])
@payment.required(get_payment_amt)
def ping():
    """
    Gets the cheapest X nodes running ping21 and runs them against the url specified.
    """
    user_input = json.loads(request.data.decode('UTF-8'))
    if 'nodes' not in user_input:
        ret_obj = {'success': False, "message": "Missing nodes parameter in post data."}
        ret = json.dumps(ret_obj, indent=2)
        return (ret, 200, {'Content-length': len(ret), 'Content-type': 'application/json'})

    if 'website' not in user_input:
        ret_obj = {'success': False, "message": "Missing website parameter in post data."}
        ret = json.dumps(ret_obj, indent=2)
        return (ret, 200, {'Content-length': len(ret), 'Content-type': 'application/json'})

    # Get the amount of nodes the user requested + 10 in case one of them fails
    requested_count = user_input['nodes']
    nodes = db.get_cheapest_nodes(requested_count + 10)

    # Iterate over the nodes returned from the DB
    vals = []
    successful_requests = 0
    for node in nodes:

        # If we have already found as many nodes as the user requested, bail out
        if successful_requests >= requested_count:
            break

        try:
            # Get the ping data from the node.
            # Use the uri from the user in the request.
            # Use the maxprice from the db (last time we saw it), so we don't get suckered.
            ret = requests.get(node['url'] + "?uri=" + user_input['website'], max_price=node['price'])

            # Get the json for the response
            ret_obj = ret.json()
            ret_obj['price_paid'] = node['price']

            # Strip out sensitive info
            del ret_obj['server']['ip']
            del ret_obj['server']['hostname']

            # Save it off
            vals.append(ret_obj)

            # Update the success count
            successful_requests = successful_requests + 1

        except Exception as err:
            logger.error("Failure: {0}".format(err))

    ret = json.dumps(vals, indent=2)
    return (ret, 200, {'Content-length': len(ret), 'Content-type': 'application/json'})


def gather_ping_node_stats():
    """
    Iterates over nodes and updates the prices and status.
    """
    while True:
        # Sleep for 8 hours before reloading the node stats
        time.sleep(60 * 60 * 8)

        nodes = db.get_node_ips()
        for node in nodes:
            logger.info("\n\nChecking for ping server on {}".format(node))
            node_up = False

            # First try port 6002
            url = "http://{}:6002/".format(node)
            manifest_url = url + "manifest"
            try:
                # If the manifest comes back, if it is running ping21 then it is up
                logger.info("Checking on port 6002 with url: {}".format(manifest_url))
                manifest = orig_requests.get(manifest_url, timeout=1)
                logger.debug("Got back the manifest")

                if "ping21" in manifest.text:
                    node_up = True
                    logger.debug("Ping21 is running on 6002 on this node")
                else:
                    logger.debug("Ping21 was not found in the manifest")
            except:
                node_up = False

            # Not found on standard node, see if it is running as a microservice
            if not node_up:
                url = "http://{}:8080/ping/".format(node)
                manifest_url = url + "manifest"
                try:
                    # If the manifest comes back, if it is running ping21 then it is up
                    logger.debug("Checking on port 8080")
                    manifest = orig_requests.get(manifest_url, timeout=1)
                    logger.debug("Got back the manifest")

                    if "ping21" in manifest.text:
                        node_up = True
                        logger.debug("Ping21 is running on 8080 on this node")
                    else:
                        logger.debug("Ping21 was not found on this node")
                except:
                    node_up = False

            # if we didn't find the ping21 service, mark the node as down
            if not node_up:
                logger.debug("Marking this node as down since Ping21 was not found")
                db.update_node(node, False, 0, "")
                continue

            # We found the node and it is running ping21, so hit the endpoint to get the price
            try:
                # If the manifest comes back, if it is running ping21 then it is up
                logger.debug("Getting ping url: {}".format(url))
                ping_res = orig_requests.get(url)

                price = int(ping_res.headers['Price'])
                db.update_node(node, True, price, url)
                logger.debug("Updated the price from the endpoint: {}".format(price))

            except Exception as err:
                logger.error("Failure: {0}".format(err))
                db.update_node(node, False, 0, url)


if __name__ == '__main__':
    import click

    @click.command()
    @click.option("-d", "--daemon", default=False, is_flag=True, help="Run in daemon mode.")
    @click.option("-l", "--log", default="ERROR", help="Logging level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    def run(daemon, log):
        """
        Run the service.
        """
        # Set logging level
        numeric_level = getattr(logging, log.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % log)
        logging.basicConfig(level=numeric_level)

        if daemon:
            pid_file = './ping-aggregator.pid'
            if os.path.isfile(pid_file):
                pid = int(open(pid_file).read())
                os.remove(pid_file)
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                except:
                    pass
            try:
                p = subprocess.Popen(['python3', 'ping-aggregator-E16-server.py'])
                open(pid_file, 'w').write(str(p.pid))
            except subprocess.CalledProcessError:
                raise ValueError("error starting ping-aggregator-E16-server.py daemon")
        else:
            # Start cleanup thread
            cleaner = Thread(target=gather_ping_node_stats, daemon=True)
            cleaner.start()

            print("Server running...")
            app.run(host='0.0.0.0', port=7018)

    run()
