from neo4j import GraphDatabase
from .types import InfoType

NEO4J_URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "pass"


class QueryBuilder:
    id = 0

    @staticmethod
    def reset():
        QueryBuilder.id = 0

    @staticmethod
    def query_create_noun_phrase(entity):
        QueryBuilder.id += 1
        eid = f'n{QueryBuilder.id}'
        string = entity['value']

        if not entity['specifiers']:
            query = f' create ({eid}:class)'
            query += f' set {eid}.name = "{entity["lemma"]}"'
        else:
            query = f' create ({eid}:instance)-[:IS_A]->(:class {{name: "{entity["lemma"]}"}})'

            for spec in entity['specifiers']:
                inner_query, inner_id, inner_str = QueryBuilder.query_create_noun_phrase(spec)
                query += inner_query

                # link the nodes
                if spec['question'] in ['care', 'ce fel de']:
                    query += f' create ({eid})-[:SPEC]->({inner_id})'
                elif spec['question'] == "al cui":
                    query += f' create ({inner_id})-[:HAS]->({eid})'

                string += " " + inner_str

            query += f' set {eid}.name = "{string}"'

        return query, eid, string

    @staticmethod
    def query_match_noun_phrase(entity):
        QueryBuilder.id += 1
        eid = f'n{QueryBuilder.id}'
        if entity['specifiers']:
            query = f' match ({eid})-[:IS_A]->({{name: "{entity["lemma"]}"}})'
        else:
            query = f' match ({eid} {{name: "{entity["lemma"]}"}})'

        for spec in entity['specifiers']:
            inner_query, inner_id = QueryBuilder.query_match_noun_phrase(spec)
            query += inner_query

            # link the nodes
            if spec['question'] in ['care', 'ce fel de']:
                query += f' match ({eid})-[:SPEC]->({inner_id})'
            elif spec['question'] == "al cui":
                query += f' match ({inner_id})-[:HAS]->({eid})'

        return query, eid


class DbBridge:
    def __init__(self):
        # create database connection and session
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(USERNAME, PASSWORD), encrypted=False)
        self.session = self.driver.session()

    def __del__(self):
        self.driver.close()

    def set_value(self, entity, value, type=InfoType.VAL):
        query, node_id, _ = QueryBuilder.query_create_noun_phrase(entity)

        if type == InfoType.VAL:
            query += f' create ({node_id})-[:{type.value}]->(:val {{value: "{value}"}})'
        elif type == InfoType.LOC:
            query_create_location, location_node_id, _ = QueryBuilder.query_create_noun_phrase(value)
            query += query_create_location
            query += f' create ({node_id})-[:{type.value}]->({location_node_id})'
        elif type in [InfoType.TIME_POINT, InfoType.TIME_START, InfoType.TIME_END, InfoType.TIME_RANGE,
                      InfoType.TIME_DURATION]:
            query += f' create ({node_id})-[:{type.value}]->(:val {{value: "{value}"}})'

        print(query)

        self.session.run(query)

    def get_value(self, entity, type=InfoType.VAL):
        query, node_id = QueryBuilder.query_match_noun_phrase(entity)
        query += f'match ({node_id})-[:{type.value}]->(val) return val'

        result = self.session.run(query)
        values = [record.value() for record in result]

        if not values:
            return "Nu știu"
        if type == InfoType.LOC:
            return values[0]['name']
        return values[0].get('value', "Nicio valoare")

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

# bridge = DbBridge()
# print(bridge.get_value())
