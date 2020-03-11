const SpeechRecognition = webkitSpeechRecognition;

let diagnosticPara = document.querySelector('.output');
let testBtn = document.querySelector('#start-btn');

let isRunning = false; // the conversion process is running
let pauseInterval = 3000; // wait a bit between 2 successive conversions
g
const trackId = 2;
const utterancesPath = '../../../Music/';

function padNumber(n, width, z) {
    z = z || '0';
    n = n + '';
    return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
}

class UtterancePlayer {
    constructor() {
        this.utteranceIdx = 0;
        this.lastUtteranceIdx = 1;
    }

    startNextUtterance() {
        // load audio file
        this.utteranceIdx++;
        this.audio = new Audio(`${utterancesPath}${trackId}_${padNumber(this.utteranceIdx, 3)}.wav`);
        this.audio.onended = () => console.log('Audio finished playing');

        // start playing
        setTimeout(() => this.audio.play().then(() => console.log("Audio started")), 800);
    }

    pendingUtterancesNum() {
        return this.lastUtteranceIdx - this.utteranceIdx;
    }

    ensureAudioStopped() {
        this.audio.pause();
    }
}

const utterancePlayer = new UtterancePlayer();

let recognition = new SpeechRecognition();
recognition.lang = 'ro-RO';
recognition.interimResults = false;
recognition.maxAlternatives = 1;
console.log("Started recognizer:", recognition.serviceURI);

function runRecognizer() {
    if (isRunning) {
        isRunning = false;
        testBtn.textContent = 'Start recognition';
        return;
    }

    isRunning = true;
    testBtn.textContent = 'Stop recognition';

    recognition.start();

    recognition.onresult = function (event) {
        // The SpeechRecognitionEvent results property returns a SpeechRecognitionResultList object
        // The SpeechRecognitionResultList object contains SpeechRecognitionResult objects.
        // It has a getter so it can be accessed like an array
        // The first [0] returns the SpeechRecognitionResult at position 0.
        // Each SpeechRecognitionResult object contains SpeechRecognitionAlternative objects that contain individual results.
        // These also have getters so they can be accessed like arrays.
        // The second [0] returns the SpeechRecognitionAlternative at position 0.
        // We then return the transcript property of the SpeechRecognitionAlternative object

        let speechResult = event.results[0][0].transcript.toLowerCase();
        const confidence = event.results[0][0].confidence.toFixed(5).toString();

        const incomplete = utterancePlayer.audio.ended ? '' : '<span style="color: #ff0026">INCOMPLETE</span>';
        diagnosticPara.innerHTML += `<li><span style="color: #009f29">${confidence}</span> ${incomplete} ${speechResult}</li>`;
    };

    recognition.onspeechend = function () {
        //recognition.stop();
        //testBtn.disabled = false;
        //testBtn.textContent = 'Start new test';
    };

    recognition.onerror = function (event) {
        testBtn.textContent = 'Start recognition';
        diagnosticPara.innerHTML += `<span> Error occurred in recognition: ${event.error} </span>`;
        isRunning = false;
        recognition.stop();
    };

    recognition.onaudiostart = function (event) {
        //Fired when the user agent has started to capture audio.
        console.log('SpeechRecognition.onaudiostart');

        // get audio to play
        utterancePlayer.startNextUtterance();
    };

    recognition.onaudioend = function (event) {
        //Fired when the user agent has finished capturing audio.
        console.log('SpeechRecognition.onaudioend');
    };

    recognition.onend = function (event) {
        //Fired when the speech recognition service has disconnected.
        console.log('SpeechRecognition.onend');

        utterancePlayer.ensureAudioStopped();
        if (isRunning && utterancePlayer.pendingUtterancesNum() > 0)
            setTimeout(() => recognition.start(), pauseInterval);
    };

    recognition.onnomatch = function (event) {
        //Fired when the speech recognition service returns a final result with no significant recognition. This may involve some degree of recognition, which doesn't meet or exceed the confidence threshold.
        console.log('SpeechRecognition.onnomatch');
    };

    recognition.onsoundstart = function (event) {
        //Fired when any sound — recognisable speech or not — has been detected.
        console.log('SpeechRecognition.onsoundstart');
    };

    recognition.onsoundend = function (event) {
        //Fired when any sound — recognisable speech or not — has stopped being detected.
        console.log('SpeechRecognition.onsoundend');
    };

    recognition.onspeechstart = function (event) {
        //Fired when sound that is recognised by the speech recognition service as speech has been detected.
        console.log('SpeechRecognition.onspeechstart');
    };

    recognition.onstart = function (event) {
        //Fired when the speech recognition service has begun listening to incoming audio with intent to recognize grammars associated with the current SpeechRecognition.
        console.log('SpeechRecognition.onstart');
    };
}

testBtn.addEventListener('click', runRecognizer);
