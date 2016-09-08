import random
import sqlite3
import threading

# DB lock for multithreaded use case
db_rlock = threading.RLock()


class SrvDb(object):
    """
    Class for interacting with the DB.
    """

    def __init__(self, filename):
        """
        Constructor.
        """
        self.conn = sqlite3.connect(filename, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def get_node_ips(self):
        """
        Return a list of nodes ordered by ip.
        """
        with db_rlock:
            # retrieve sorted node list
            rows = []
            for row in self.cursor.execute("SELECT * FROM nodes ORDER BY ip"):
                rows.append(row[0])
            return rows

    def add_node(self, ip, up, price, url):
        """
        Add a node to the DB.
        """
        with db_rlock:

            # Add hash metadata to db
            self.cursor.execute("INSERT INTO nodes VALUES(?, ?, ?, ?)", (ip, up, price, url))
            self.conn.commit()

            return True

    def update_node(self, ip, up, price, url):
        """
        Updates an existing node in the db.
        """
        with db_rlock:
            query = "UPDATE nodes SET up=?, price=?, url=? WHERE ip=?"
            self.cursor.execute(query, (up, price, url, ip))
            self.conn.commit()

        return True

    def get_node(self, ip):
        """
        Find a node by IP.
        """
        with db_rlock:

            row = self.cursor.execute("SELECT * FROM nodes WHERE ip = ?", (ip,)).fetchone()
            if not row:
                return None
            obj = {
                'ip': row[0],
                'up': row[1] > 0,
                'price': int(row[2]),
                'url': row[3]
            }
            return obj

    def get_cheapest_nodes(self, num_nodes):
        """
        Selects the lowest priced N nodes that are up.
        """
        with db_rlock:

            # retrieve sorted node list of "up" ips
            rows = []
            count = 0
            cheapest_price = 0
            for row in self.cursor.execute("SELECT * FROM nodes WHERE up=1 ORDER BY price ASC"):

                # Check to see if we are over the requested count
                count = count + 1
                if count > num_nodes:
                    # If the next node we are looking at has a higher price, then we can bail.
                    # Otherwize we will add it to the list for consideration.
                    if int(row[2]) > cheapest_price:
                        break

                obj = {
                    'ip': row[0],
                    'up': row[1] > 0,
                    'price': int(row[2]),
                    'url': row[3],
                }
                rows.append(obj)
                cheapest_price = int(row[2])

            # Return a random subset of the cheapest nodes (count of num_nodes)
            return random.sample(rows, num_nodes)

    def delete_node(self, ip):
        """
        Delete the node from the DB.
        """
        with db_rlock:

            self.cursor.execute("DELETE FROM nodes WHERE ip = ?", (ip))
            self.conn.commit()
