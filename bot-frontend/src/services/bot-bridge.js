import axios from 'axios';

const BOT_ENDPOINT = 'http://127.0.0.1:5005/webhooks/rest/webhook';

export const sendMsgAndGetReply = async (msg) => {
    const response = await axios.post(BOT_ENDPOINT, {
        sender: "anonymus",
        message: msg
    });

    return response.data?.[0]?.text || "Am întâmpinat o eroare 😥";
};