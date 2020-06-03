import axios from 'axios';

export const sendMsgAndGetReply = async (msg) => {
    // axios.post();

    await new Promise(resolve => {
        setTimeout(() => {
            resolve();
        }, 2000);
    });
    const botReply = "RASA replied";
    return botReply;
};