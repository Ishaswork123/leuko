document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const imagePreview = document.getElementById('image-preview');
    const uploadStatus = document.getElementById('upload-status');
    const resultsPlaceholder = document.getElementById('results-placeholder');
    const resultsArea = document.getElementById('results-area');

    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatWindow = document.getElementById('chat-window');
    const closeChat = document.getElementById('close-chat');
    const sendChat = document.getElementById('send-chat');
    const chatInput = document.getElementById('chat-input-field');
    const chatMessages = document.getElementById('chat-messages');

    // --- Drag & Drop ---
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    fileInput.addEventListener('change', () => {
        handleFiles(fileInput.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            previewFile(file);
            uploadFile(file);
        }
    }

    function previewFile(file) {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onloadend = () => {
            imagePreview.src = reader.result;
            imagePreview.style.display = 'block';
            dropZone.querySelector('.upload-icon').style.display = 'none';
            dropZone.querySelector('p').style.display = 'none';
            dropZone.querySelector('small').style.display = 'none';
        }
    }

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        uploadStatus.style.display = 'block';
        uploadStatus.innerHTML = '<i class="fas fa-sync fa-spin"></i> Processing biopsy sample...';
        resultsPlaceholder.style.display = 'block';
        resultsArea.style.display = 'none';

        fetch('/predict', {
            method: 'POST',
            body: formData
        })
            .then(async (response) => {
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Server error');
                return data;
            })
            .then(data => {
                uploadStatus.style.display = 'none';
                resultsPlaceholder.style.display = 'none';
                resultsArea.style.display = 'flex';

                document.getElementById('prediction-label').innerText = `Prediction: ${data.prediction}`;
                document.getElementById('confidence-score').innerText = `Confidence: ${(data.confidence * 100).toFixed(2)}%`;
                document.getElementById('heatmap-img').src = data.heatmap_url + '?t=' + new Date().getTime(); // Prevent caching
            })
            .catch(error => {
                console.error('Error:', error);
                uploadStatus.innerHTML = `<span style="color:red">Error: ${error.message}</span>`;
                resultsPlaceholder.innerHTML = `<p style="color:red">Analysis failed. Please check server logs.</p>`;
            });
    }

    // --- Chatbot Logic ---
    chatbotToggle.addEventListener('click', () => {
        chatWindow.classList.toggle('active');
    });

    closeChat.addEventListener('click', () => {
        chatWindow.classList.remove('active');
    });

    sendChat.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        appendMessage('user', text);
        chatInput.value = '';

        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        })
            .then(async (response) => {
                const data = await response.json();
                if (!response.ok) throw new Error(data.response || 'Chat failed');
                return data;
            })
            .then(data => {
                appendMessage('bot', data.response);
            })
            .catch(error => {
                appendMessage('bot', `System Error: ${error.message}`);
            });
    }

    function appendMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        msgDiv.innerText = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
