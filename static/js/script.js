async function sendMessage() {

    let input = document.getElementById("user-input");

    let message = input.value;

    if (message.trim() === "") {

        return;
    }

    let chatBox = document.getElementById("chat-box");

    // ===== USER MESSAGE =====

    chatBox.innerHTML += `

        <div class="user-message">

            ${message}

        </div>

    `;

    input.value = "";

    // ===== LOADING MESSAGE =====

    chatBox.innerHTML += `

        <div class="bot-message" id="loading">

            ⏳ AI is typing...

        </div>

    `;

    // ===== AUTO SCROLL =====

    chatBox.scrollTop = chatBox.scrollHeight;

    try {

        // ===== FETCH RESPONSE =====

        let response = await fetch("/chat", {

            method: "POST",

            headers: {

                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                message: message
            })
        });

        let data = await response.json();

        // ===== REMOVE LOADING =====

        document.getElementById("loading").remove();

        // ===== BOT MESSAGE =====

        chatBox.innerHTML += `

        <div class="bot-message">

            ${data.reply}

        </div>

        `;

        // ===== BOT VOICE =====

        speakText(data.reply);

        // ===== AUTO SCROLL =====

        chatBox.scrollTop = chatBox.scrollHeight;

    }

    catch (error) {

        document.getElementById("loading").remove();

        chatBox.innerHTML += `

            <div class="bot-message">

                ⚠️ Error getting response.

            </div>

        `;

        chatBox.scrollTop = chatBox.scrollHeight;
    }
}


// =====================================
// ENTER KEY SUPPORT
// =====================================

document.getElementById(
    "user-input"
).addEventListener(

    "keypress",

    function(event) {

        if (event.key === "Enter") {

            event.preventDefault();

            sendMessage();
        }
    }
);


// =====================================
// HELP MODAL
// =====================================

function openHelp() {

    document.getElementById(
        "helpModal"
    ).style.display = "block";
}

function closeHelp() {

    document.getElementById(
        "helpModal"
    ).style.display = "none";
}


// =====================================
// QUICK SUPPORT POPUP
// =====================================

function togglePopup(){

    let popup = document.getElementById("popupBox");

    if(popup.style.display === "flex"){

        popup.style.display = "none";

    }else{

        popup.style.display = "flex";
    }
}


function sendQuickMessage(message){

    document.getElementById(
        "popupBox"
    ).style.display = "none";

    fetch("/chat", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            message: message
        })

    })

    .then(response => response.json())

    .then(data => {

        let chatBox =
            document.getElementById("chat-box");

        // ===== USER MESSAGE =====

        chatBox.innerHTML += `

        <div class="user-message">
            ${message}
        </div>

        `;

        // ===== BOT MESSAGE =====

        chatBox.innerHTML += `

        <div class="bot-message">
            ${data.reply}
        </div>

        `;

        // ===== BOT VOICE =====

        speakText(data.reply);

        // ===== AUTO SCROLL =====

        chatBox.scrollTop =
            chatBox.scrollHeight;

    })

    .catch(error => {

        console.log(error);
    });
}


// =====================================
// CHAT LIMIT POPUP
// =====================================

function showPopup(message){

    document.getElementById(
        "popupMessage"
    ).innerText = message;

    document.getElementById(
        "limitPopup"
    ).style.display = "flex";
}


function closePopup(){

    document.getElementById(
        "limitPopup"
    ).style.display = "none";
}


// =====================================
// BOT VOICE RESPONSE
// =====================================

window.speakText = function (text) {

    window.speechSynthesis.cancel();

    let speech =
        new SpeechSynthesisUtterance(text);

    speech.text = text;

    speech.lang = "en-US";

    speech.volume = 1;

    speech.rate = 1;

    speech.pitch = 1;

    window.speechSynthesis.speak(speech);
};