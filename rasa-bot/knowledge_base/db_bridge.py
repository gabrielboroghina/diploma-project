from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "pass"


class DbBridge:
    def __init__(self):
        # create database connection and session
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(USERNAME, PASSWORD), encrypted=False)
        self.session = self.driver.session()

    def __del__(self):
        self.driver.close()

    def set_attr(self, entity_name, attr):
        attr_name, attr_val = attr
        print(f"[DB] Setting attribute to {entity_name} -> {attr_name}:{attr_val}")

        self.session.run('merge (ent {name: $ent_name})'
                         'create (attr {value: $attr_val})'
                         'create (ent)-[:ATTR {name: $attr_name}]->(attr)',
                         ent_name=entity_name, attr_name=attr_name, attr_val=attr_val)

    def get_attr(self, entity_name, attr_name):
        result = self.session.run('match (p {name: $name})-[:ATTR {name: $attr_name}]->(attr)'
                                  'return attr.value', name=entity_name, attr_name=attr_name)

        values = [record.value() for record in result]
        return "Nu știu" if not values else values[0]

#
# bridge = DbBridge()
# print(bridge.get_attr("mariei", "interfonul"))
