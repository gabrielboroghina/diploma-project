import axios from 'axios';

const API_HOST = 'http://127.0.0.1:5005';
const BOT_ENDPOINT = `${API_HOST}/webhooks/rest/webhook`;
const PREDICT_ENDPOINT = `${API_HOST}/conversations/0/messages`;

export const sendMsgAndGetReply = async (msg) => {
    const [response, prediction] = await Promise.all([
        axios.post(BOT_ENDPOINT, {
            sender: "anonymus",
            message: msg
        }),
        axios.post(PREDICT_ENDPOINT, {
            sender: "user",
            text: msg
        })]);

    return [
        response.data?.[0]?.text || "Am întâmpinat o eroare 😥",
        prediction.data.latest_message.intent
    ];
};