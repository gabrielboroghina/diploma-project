# Memory assistant conversational agent

## Running the bot

1. Start the Neo4j database
2. Start the RASA action server: ``rasa run actions``
3. Launch the RASA bot: ``rasa shell``
4. Type your utterances

#### Run HTTP server
`rasa run --enable-api -m models/20200515-103715.tar.gz
`

Test NLU:
 
`curl localhost:5005/model/parse -d '{"text":"hello"}'`