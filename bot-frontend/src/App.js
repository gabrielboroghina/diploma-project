import React, {useState} from 'react';
import './App.css';
import SpeechToText from "./services/speech-to-text";
import {sendMsgAndGetReply} from "./services/bot-bridge";

function App() {
    const [messages, setMessages] = useState([]);

    const sendUserInput = (msg, speechToTextConfidence) => {
        setMessages(messages => [
            ...messages,
            {
                author: "me",
                text: msg,
                metadata: speechToTextConfidence ? `speech-to-text confidence: ${speechToTextConfidence}` : "typed"
            }
        ]);

        setMessages(messages => [
            ...messages,
            {
                author: "bot",
                text: null
            }
        ]);

        sendMsgAndGetReply(msg).then((reply) => {
            setMessages(messages => [
                ...messages.slice(0, -1),
                {
                    author: "bot",
                    text: reply
                }
            ]);
        });
    };

    return (
        <div className="container">
            <div className="scrollable-pane">
                <div className="wrapper">
                    {messages.map((msg, idx) => (
                        <MessageBubble author={msg.author} msg={msg.text} metadata={msg.metadata}
                                       key={idx}/>
                    ))}
                </div>
            </div>

            <InputBox onUserMessage={sendUserInput}/>
        </div>
    );
}

const InputBox = (props) => {
    const onUserVoiceInput = (msg, confidence) => {
        props.onUserMessage(msg, confidence);
    };

    const speechToTextConverter = new SpeechToText(onUserVoiceInput);

    const sendUserInput = () => {
        const inputTextField = document.getElementById("input");
        const message = inputTextField.value;
        inputTextField.value = "";

        props.onUserMessage(message);
    };

    return (
        <div className="input-box">
            <button className="icon-btn tooltip" onClick={() => speechToTextConverter.execute()}>
                <i className="fas fa-microphone"/>
                <span className="tooltip-text">Utter a request</span>
            </button>

            <input id="input" className="text-field" type="text"
                   placeholder="Type a question or a store request"
                   autoComplete="off"
                   onKeyDown={e => {
                       if (e.key === "Enter") {
                           e.preventDefault();
                           sendUserInput();
                       }
                   }}
            />
            <button className="icon-btn" onClick={sendUserInput}>
                <i className="fas fa-paper-plane"/>
            </button>
        </div>
    );
};

const MessageBubble = (props) => {
    return (
        <div className="stack-layer">
            {
                props.metadata &&
                <p className="bubble-metadata" style={{textAlign: props.author === "me" ? "right" : "left"}}>
                    {props.metadata}
                </p>
            }
            <div className={"bubble " + (props.author === "me" ? "bubble-right" : "bubble-left")}>
                {
                    props.msg
                        ? props.msg
                        : <TypingIndicator/>
                }
            </div>
        </div>
    );
};

const TypingIndicator = () => (
    <div className="ticontainer">
        <div className="tiblock">
            <div className="tidot"/>
            <div className="tidot"/>
            <div className="tidot"/>
        </div>
    </div>
);

export default App;
