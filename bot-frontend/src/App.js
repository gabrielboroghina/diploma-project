import React, {useState} from 'react';
import './App.css';

function App() {
    const [messages, setMessages] = useState([]);

    const sendUserInput = msg => {
        setMessages(messages => [
            ...messages,
            {
                author: "me",
                text: msg
            }
        ]);
    };

    return (
        <div className="container">
            <div className="scrollable-pane">
                {messages.map(msg => (
                    <MessageBubble author={msg.author} msg={msg.text}/>
                ))}
            </div>
            <InputBox onUserMessage={sendUserInput}/>
        </div>
    );
}

const InputBox = (props) => {
    const sendUserInput = () => {
        const inputTextField = document.getElementById("input");
        const message = inputTextField.value;

        props.onUserMessage(message);

        inputTextField.value = "";
    };

    return (
        <div className="input-box">
            <button className="icon-btn">
                <i className="fas fa-microphone"/>
            </button>
            <input id="input" className="text-field" type="text"
                   placeholder="Type a question or a store request"
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
            <div className={"bubble " + (props.author === "me" ? "bubble-right" : "bubble-left")}>
                {props.msg}
            </div>
        </div>
    );
};

export default App;
