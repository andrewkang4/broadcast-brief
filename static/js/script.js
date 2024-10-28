document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const output = document.getElementById('output');
    const processedOutput = document.getElementById('processedOutput');

    let recognition;
    let finalTranscript = '';
    let interimTranscript = '';

    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        // Configure to include punctuation
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onstart = () => {
            startButton.disabled = true;
            stopButton.disabled = false;
        };

        recognition.onend = () => {
            startButton.disabled = false;
            stopButton.disabled = true;
        };

        recognition.onresult = (event) => {
            interimTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                    processSentence(improveTranscriptPunctuation(event.results[i][0].transcript));
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
            output.innerHTML = finalTranscript + '<i style="color: #888;">' + interimTranscript + '</i>';
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
        };

        startButton.onclick = () => {
            finalTranscript = '';
            recognition.start();
            startWebcam();
        };

        stopButton.onclick = () => {
            recognition.stop();
            stopWebcam();
        };
    } else {
        startButton.style.display = 'none';
        stopButton.style.display = 'none';
        output.innerHTML = 'Web Speech API is not supported in this browser.';
    }

    function improveTranscriptPunctuation(transcript) {
        // Add a period at the end of the sentence if it's missing
        transcript = transcript.trim();
        if (!transcript.endsWith('.') && !transcript.endsWith('!') && !transcript.endsWith('?')) {
            transcript += '.';
        }

        // Capitalize the first letter of the sentence
        transcript = transcript.charAt(0).toUpperCase() + transcript.slice(1);

        // Add commas after long pauses (represented by multiple spaces)
        transcript = transcript.replace(/\s{3,}/g, ', ');

        return transcript;
    }

    function processSentence(sentence) {
        const canvas = document.createElement('canvas');
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        canvas.getContext('2d').drawImage(videoElement, 0, 0);

        const base64Image = canvas.toDataURL('image/jpeg');

        fetch('/process_sentence', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ sentence: sentence, image: base64Image }),
        })
        .then(response => response.json())
        .then(data => {
            processedOutput.innerHTML += data.processed_sentence + ' ';
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
});

let webcamStream;
let captureInterval;
const CAPTURE_INTERVAL = 10000; // 10 seconds

const videoElement = document.getElementById('webcam');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const imageContainer = document.getElementById('imageContainer');

async function startWebcam() {
    try {
        webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
        videoElement.srcObject = webcamStream;
    } catch (error) {
        console.error('Error accessing webcam:', error);
        alert('Unable to access webcam. Please make sure you have granted permission.');
    }
}

function stopWebcam() {
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        videoElement.srcObject = null;
    }
}

async function captureScreenshot() {
    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    canvas.getContext('2d').drawImage(videoElement, 0, 0);

    const base64Image = canvas.toDataURL('image/jpeg');

    try {
        const response = await fetch('/save-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: base64Image }),
        });

        if (response.ok) {
            console.log('Image sent to server successfully');
            displayImage(base64Image);
        } else {
            console.error('Failed to send image to server');
        }
    } catch (error) {
        console.error('Error sending image to server:', error);
    }
}

function displayImage(base64Image) {
    const img = document.createElement('img');
    img.src = base64Image;
    img.className = 'img-thumbnail m-1';
    img.style.width = '100px';
    img.style.height = '75px';
    imageContainer.appendChild(img);
}

function loadSavedImages() {
    // This function is no longer needed as we're not using localStorage
    // We can implement server-side image loading in the future if required
}

// Remove the loadSavedImages call as it's no longer needed
// window.addEventListener('load', loadSavedImages);
