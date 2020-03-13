import mysql.connector


class DexBridge:
    def __init__(self):
        self.__cnx = mysql.connector.connect(user='root', password='npdg13d', database='dexonline')
        self.__cursor = self.__cnx.cursor()

    def __del__(self):
        #        self.__cursor.close()
        self.__cnx.close()

    def lemmaForWord(self, word, pos=None):
        query = (
            "SELECT mt.description, l.formNoAccent, f.formNoAccent, i.gender, i.number, i.animate, f.variant FROM Lexeme l "
            "join InflectedForm f on l.id = f.lexemeId "
            "join Inflection i on f.inflectionId = i.id "
            "join modeltype mt on l.modelType = mt.code "
            "where f.formNoAccent = %(word)s "
            "order by i.rank, f.variant;")

        self.__cursor.execute(query, {'word': word})

        entries = [entry for entry in self.__cursor]

        if len(entries) == 1:
            return entries[0][1]
        elif pos:
            for tup in entries:
                if pos in tup[0]:
                    return tup[1]
            # print(tup[2], '->', tup[1], ' | ', tup[0])

        if not entries:
            return word
        return [(entry[0], entry[1]) for entry in entries]
