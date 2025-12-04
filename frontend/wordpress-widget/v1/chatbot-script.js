// Chat Widget State
let isOpen = false;
let conversationHistory = [];
let currentLanguage = 'EN'; // Default language
let faqCache = {}; // Cache for FAQ responses
let faqsHidden = false; // Track if FAQs are hidden
let currentAbortController = null; // For cancelling requests
let currentStreamingMessage = null; // Reference to the message being streamed
let isVoiceEnabled = false; // Voice toggle state
let recognition = null; // Speech recognition instance
let isListening = false; // Microphone listening state

// Audio player state for TTS
let currentAudio = null;  // HTML5 Audio instance
let currentAudioBlob = null;  // Blob URL for cleanup
let audioCache = [];  // Store last 3 audio blobs with TTL
const MAX_AUDIO_CACHE_SIZE = 3;
const AUDIO_TTL = 5 * 60 * 1000; // 5 minutes in milliseconds

// Configuration
const API_BASE_URL = 'http://localhost:8000';  // Change to your backend URL
const API_ENDPOINT = '/api/v1/chat/';
const STREAM_ENDPOINT = '/api/v1/chat/stream';
// const FAQ_ENDPOINT = '/api/v1/faqs/'; // No longer needed - FAQs are hardcoded
const USE_STREAMING = true; // Toggle streaming vs regular

// Hardcoded FAQ data - No API calls needed for instant response
const HARDCODED_FAQS = {
    services: {
        id: "services",
        question: {
            EN: "What services do you provide?",
            DE: "Welche Leistungen bieten Sie an?",
            FR: "Quels services proposez-vous ?"
        },
        answer: {
            EN: "We offer a comprehensive range of medical, therapeutic, and integrative health services designed to support diagnostics, treatment, rehabilitation, and long-term wellbeing. Our core service areas include:\n\n**1. Osteopathy:** Classical osteopathy, pediatric osteopathy, osteopathy for pregnant women, and sports osteopathy to support functional balance, healthy development, relief during pregnancy, and performance enhancement for athletes.\n\n**2. Physiotherapy:** Classic physiotherapy for musculoskeletal conditions, pediatric physiotherapy for motor development, and flexible self-pay physiotherapy to reduce pain, improve mobility, and enhance performance at all ages.\n\n**3. Medicine:** Specialized services in orthopedics & traumatology, rheumatology, internal medicine, occupational therapy, and stem cell therapy for precise diagnostics, targeted treatment, functional rehabilitation, and long-term health support.\n\n**4. Complementary Medicine:** Acupuncture, homeopathy, medical massages, and colon hydrotherapy to promote natural regeneration, relaxation, inner balance, and complement conventional treatments.\n\n**5. Integrative Medicine:** Combines medical diagnostics with therapies such as orthomolecular medicine, phytotherapy, functional myodiagnostics, neural therapy, ozone therapy, and colon hydrotherapy to activate self-healing and support gut health, hormones, detoxification, mitochondria, micronutrients, and mental resilience.\n\n**6. FunctioTraining:** Personalized, structured training programs for rehabilitation, performance, and long-term fitness. Flexible memberships allow independent, professionally guided training, with optional outdoor functiowalks for extra activity and energy.",
            DE: "Wir bieten ein umfassendes Spektrum an medizinischen, therapeutischen und integrativen Gesundheitsdienstleistungen zur Unterstützung von Diagnostik, Behandlung, Rehabilitation und langfristigem Wohlbefinden. Unsere Kernbereiche umfassen:\n\n**1. Osteopathie:** Klassische Osteopathie, Kinderosteopathie, Osteopathie für Schwangere und Sportosteopathie zur Unterstützung der funktionellen Balance, gesunden Entwicklung, Linderung während der Schwangerschaft und Leistungssteigerung bei Sportlern.\n\n**2. Physiotherapie:** Klassische Physiotherapie für muskuloskelettale Beschwerden, Kinderphysiotherapie zur motorischen Entwicklung und flexible Selbstzahler-Physiotherapie zur Schmerzlinderung, Verbesserung der Beweglichkeit und Leistungssteigerung in jedem Alter.\n\n**3. Medizin:** Spezialisierte Leistungen in Orthopädie & Traumatologie, Rheumatologie, Innere Medizin, Ergotherapie und Stammzelltherapie für präzise Diagnostik, gezielte Behandlung, funktionelle Rehabilitation und langfristige Gesundheitsunterstützung.\n\n**4. Komplementärmedizin:** Akupunktur, Homöopathie, medizinische Massagen und Colon-Hydrotherapie zur Förderung natürlicher Regeneration, Entspannung, innerer Balance und als Ergänzung zur Schulmedizin.\n\n**5. Integrative Medizin:** Kombination aus medizinischer Diagnostik und Therapien wie orthomolekulare Medizin, Phytotherapie, funktionelle Myodiagnostik, Neuraltherapie, Ozontherapie und Colon-Hydrotherapie zur Aktivierung der Selbstheilungskräfte und Unterstützung von Darmgesundheit, Hormonen, Entgiftung, Mitochondrien, Mikronährstoffen und mentaler Resilienz.\n\n**6. FunctioTraining:** Personalisierte, strukturierte Trainingsprogramme für Rehabilitation, Leistungssteigerung und langfristige Fitness. Flexible Mitgliedschaften ermöglichen unabhängiges, professionell begleitetes Training, optional ergänzt durch Functiowalks im Freien für zusätzliche Bewegung und Energie.",
            FR: "Nous offrons une gamme complète de services médicaux, thérapeutiques et de santé intégrative pour soutenir le diagnostic, le traitement, la rééducation et le bien-être à long terme. Nos principaux domaines de services comprennent :\n\n**1. Ostéopathie :** Ostéopathie classique, ostéopathie pédiatrique, ostéopathie pour femmes enceintes et ostéopathie sportive pour soutenir l'équilibre fonctionnel, le développement sain, le soulagement pendant la grossesse et l'amélioration des performances sportives.\n\n**2. Physiothérapie :** Physiothérapie classique pour les troubles musculo-squelettiques, physiothérapie pédiatrique pour le développement moteur et physiothérapie en paiement libre pour réduire la douleur, améliorer la mobilité et les performances à tous les âges.\n\n**3. Médecine :** Services spécialisés en orthopédie & traumatologie, rhumatologie, médecine interne, ergothérapie et thérapie par cellules souches pour un diagnostic précis, un traitement ciblé, une rééducation fonctionnelle et un soutien à long terme de la santé.\n\n**4. Médecine complémentaire :** Acupuncture, homéopathie, massages médicaux et hydrothérapie colique pour favoriser la régénération naturelle, la relaxation, l'équilibre intérieur et compléter les traitements conventionnels.\n\n**5. Médecine intégrative :** Combine le diagnostic médical avec des thérapies telles que la médecine orthomoléculaire, la phytothérapie, le myodiagnostic fonctionnel, la thérapie neurale, l'ozonothérapie et l'hydrothérapie colique pour activer l'auto-guérison et soutenir la santé intestinale, hormonale, la détoxification, les mitochondries, les micronutriments et la résilience mentale.\n\n**6. FunctioTraining :** Programmes d'entraînement personnalisés et structurés pour la rééducation, l'amélioration des performances et la forme physique à long terme. Les abonnements flexibles permettent un entraînement indépendant mais guidé professionnellement, avec des Functiowalks en extérieur en option pour plus de mouvement et d'énergie."
        },
        category: "services"
    },
    physiotherapy: {
        id: "physiotherapy",
        question: {
            EN: "Tell me about physiotherapy",
            DE: "Erzählen Sie mir etwas über Physiotherapie",
            FR: "Parlez-moi de la physiothérapie"
        },
        answer: {
            EN: "Our physiotherapy services focus on restoring and improving physical function through targeted, evidence-based treatments tailored to your individual needs.\n\n**1. Physiotherapy:** Enhance mobility, strength, and functional capacity while sustainably reducing pain. Treatments are active, personalized, and evidence-based for long-term recovery and improved quality of life.\n\n**2. Child Physiotherapy:** Supports children's physical development through playful exercises, promoting motor skills, movement quality, coordination, and independence during key growth phases.\n\n**3. Self-Pay Physiotherapy:** Offers goal-oriented treatments and precise testing procedures for individualized care, allowing you to actively manage your health and achieve optimal results.",
            DE: "Unsere Physiotherapie-Dienstleistungen konzentrieren sich darauf, die körperliche Funktion gezielt wiederherzustellen und zu verbessern – durch evidenzbasierte, individuell abgestimmte Behandlungen.\n\n**1. Physiotherapie:** Steigerung von Beweglichkeit, Kraft und Funktionalität bei nachhaltiger Schmerzreduktion. Die Behandlungen sind aktiv, personalisiert und evidenzbasiert für langfristige Genesung und verbesserte Lebensqualität.\n\n**2. Kinderphysiotherapie:** Unterstützt die körperliche Entwicklung von Kindern durch spielerische Übungen, fördert motorische Fähigkeiten, Bewegungsqualität, Koordination und Selbstständigkeit während wichtiger Wachstumsphasen.\n\n**3. Selbstzahler-Physiotherapie:** Bietet zielgerichtete Behandlungen und präzise Testverfahren für eine individuelle Betreuung, damit Sie Ihre Gesundheit aktiv steuern und optimale Ergebnisse erzielen können.",
            FR: "Nos services de physiothérapie visent à restaurer et améliorer la fonction physique grâce à des traitements ciblés et basés sur des preuves, adaptés à vos besoins individuels.\n\n**1. Physiothérapie :** Améliorer la mobilité, la force et la capacité fonctionnelle tout en réduisant durablement la douleur. Les traitements sont actifs, personnalisés et basés sur les dernières preuves médicales pour une récupération à long terme et une meilleure qualité de vie.\n\n**2. Physiothérapie pour enfants :** Soutient le développement physique des enfants grâce à des exercices ludiques, favorisant les compétences motrices, la qualité du mouvement, la coordination et l'indépendance pendant les phases de croissance clés.\n\n**3. Physiothérapie en paiement libre :** Propose des traitements ciblés et des tests précis pour des soins individualisés, vous permettant de gérer activement votre santé et d'obtenir des résultats optimaux."
        },
        category: "services"
    },
    appointment: {
        id: "appointment",
        question: {
            EN: "How to book an appointment?",
            DE: "Wie buche ich einen Termin?",
            FR: "Comment prendre rendez-vous ?"
        },
        answer: {
            EN: "**Booking link:** [Click here to book online](https://functiomed.thefotoloft.ch/pages/online-termin-buchen/)\n\n**Step-by-Step Guide:**\n**1. Select Treatment & Reason:** Choose your specialty and reason for consultation.\n**2. Choose Practitioner:** Pick your preferred doctor or therapist or view all available appointments.\n**3. Select Time Slot:** Browse the calendar and select a suitable date and time.\n**4. Enter Email:** Provide a valid email to continue and confirm booking.\n**5. Medicosearch Registration:** Enter first name, last name, and password to create an account, and accept Privacy Policy and Terms & Conditions.\n**6. Confirm Booking:** Submit email and account details to finalize your appointment.",
            DE: "**Buchungslink:** [Hier klicken zum Online-Buchen](https://functiomed.thefotoloft.ch/pages/online-termin-buchen/)\n\n**Schritt-für-Schritt-Anleitung:**\n**1. Behandlung & Grund auswählen:** Wählen Sie Ihre Fachrichtung und den Grund für die Konsultation.\n**2. Behandler wählen:** Wählen Sie Ihren bevorzugten Arzt oder Therapeuten oder zeigen Sie alle verfügbaren Termine an.\n**3. Zeitfenster auswählen:** Durchsuchen Sie den Kalender und wählen Sie ein passendes Datum und Uhrzeit.\n**4. E-Mail eingeben:** Geben Sie eine gültige E-Mail-Adresse ein, um die Buchung fortzusetzen und zu bestätigen.\n**5. Medicosearch-Registrierung:** Geben Sie Vorname, Nachname und Passwort ein, um ein Konto zu erstellen, und akzeptieren Sie Datenschutzbestimmungen und AGB.\n**6. Buchung bestätigen:** Senden Sie Ihre E-Mail und Kontodaten, um den Termin abzuschließen.",
            FR: "**Lien de réservation :** [Cliquez ici pour réserver en ligne](https://functiomed.thefotoloft.ch/pages/online-termin-buchen/)\n\n**Guide étape par étape :**\n**1. Sélectionner le traitement et le motif :** Choisissez votre spécialité et le motif de la consultation.\n**2. Choisir le praticien :** Sélectionnez votre médecin ou thérapeute préféré ou affichez tous les rendez-vous disponibles.\n**3. Choisir l'horaire :** Parcourez le calendrier et sélectionnez une date et une heure appropriées.\n**4. Saisir l'e-mail :** Fournissez une adresse e-mail valide pour continuer et confirmer la réservation.\n**5. Inscription sur Medicosearch :** Entrez votre prénom, nom et mot de passe pour créer un compte, et acceptez la politique de confidentialité et les conditions générales.\n**6. Confirmer la réservation :** Soumettez vos coordonnées e-mail et de compte pour finaliser votre rendez-vous."
        },
        category: "booking"
    },
    contact: {
        id: "contact",
        question: {
            EN: "How do I contact you?",
            DE: "Wie kann ich Sie kontaktieren?",
            FR: "Comment puis-je vous contacter ?"
        },
        answer: {
            EN: "You can contact us by phone or email:\n\n**Phone:** +41 (0)44 401 15 15\n**Email:** functiomed@hin.ch\n\nWe usually respond to inquiries within **24 hours** on **weekdays**.",
            DE: "Sie können uns telefonisch oder per E-Mail kontaktieren:\n\n**Telefon:** +41 (0)44 401 15 15\n**E-Mail:** functiomed@hin.ch\n\nWir beantworten Anfragen in der Regel innerhalb von **24 Stunden** an **Werktagen**.",
            FR: "Vous pouvez nous contacter par téléphone ou par e-mail :\n\n**Téléphone :** +41 (0)44 401 15 15\n**E-mail :** functiomed@hin.ch\n\nNous répondons généralement aux demandes dans les **24 heures** en **semaine**."
        },
        category: "contact"
    },
    hours: {
        id: "hours",
        question: {
            EN: "What are your hours?",
            DE: "Wie sind Ihre Öffnungszeiten?",
            FR: "Quels sont vos horaires ?"
        },
        answer: {
            EN: "Our regular opening hours are **Monday to Friday, from 08:00 to 18:00**. Appointments outside these hours are possible by arrangement.",
            DE: "Unsere regulären Öffnungszeiten sind **Montag bis Freitag, von 08:00 bis 18:00 Uhr**. Termine außerhalb dieser Zeiten sind nach Vereinbarung möglich.",
            FR: "Nos heures d'ouverture régulières sont du **lundi au vendredi, de 08h00 à 18h00**. Des rendez-vous en dehors de ces heures sont possibles sur arrangement."
        },
        category: "general"
    }
};

// Language-specific messages
const MESSAGES = {
    EN: {
        initialGreeting: "Hi there! 👋 I'm FIONA, your friendly assistant at Functiomed. I'm here to help you with anything you need - whether it's finding information about our services, doctors, or answering your questions. What can I help you with today?",
        placeholder: "Type your message or click mic to speak...",
        errorMessage: "Sorry, there was an error. Please try again.",
        typingIndicator: "Typing...",
        headerTitle: "FIONA",
        headerStatus: "● Online",
        ttsError: "Could not play audio. Please try again."
    },
    DE: {
        initialGreeting: "Hallo! 👋 Ich bin FIONA, Ihre freundliche Assistentin bei Functiomed. Ich bin hier, um Ihnen bei allem zu helfen, was Sie brauchen - ob es darum geht, Informationen über unsere Dienstleistungen, Ärzte zu finden oder Ihre Fragen zu beantworten. Womit kann ich Ihnen heute helfen?",
        placeholder: "Geben Sie Ihre Nachricht ein...",
        errorMessage: "Entschuldigung, es gab einen Fehler. Bitte versuchen Sie es erneut.",
        typingIndicator: "Tippt...",
        headerTitle: "FIONA",
        headerStatus: "● Online",
        ttsError: "Audio konnte nicht abgespielt werden. Bitte versuchen Sie es erneut."
    },
    FR: {
        initialGreeting: "Bonjour ! 👋 Je suis FIONA, votre assistante amicale chez Functiomed. Je suis là pour vous aider avec tout ce dont vous avez besoin - que ce soit pour trouver des informations sur nos services, nos médecins ou répondre à vos questions. En quoi puis-je vous aider aujourd'hui ?",
        placeholder: "Tapez votre message...",
        errorMessage: "Désolé, une erreur s'est produite. Veuillez réessayer.",
        typingIndicator: "Écrit...",
        headerTitle: "FIONA",
        headerStatus: "● En ligne",
        ttsError: "Impossible de lire l'audio. Veuillez réessayer."
    }
};

// DOM Elements
const chatButton = document.getElementById('chatButton');
const chatWidget = document.getElementById('chatWidget');
const closeButton = document.getElementById('closeButton');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendButton');
const typingIndicator = document.getElementById('typingIndicator');
const stopButton = document.getElementById('stopButton');
const voiceToggle = document.getElementById('voiceToggle');
const micButton = document.getElementById('micButton');
const pitchAnimation = document.getElementById('pitchAnimation');

// Initialize
function init() {
    // Check if WordPress config exists, otherwise use defaults
    if (typeof chatbotConfig !== 'undefined') {
        currentLanguage = chatbotConfig.language || 'DE';
    }

    setInitialTime();
    updateLanguageUI();
    setupEventListeners();
    setupLanguageSelector();
    setupFAQButtons();
    loadFAQs(); // Pre-load FAQ data
}

// Setup language selector event listener
function setupLanguageSelector() {
    const languageSelect = document.getElementById('languageSelect');

    // Set initial value
    if (languageSelect) {
        languageSelect.value = currentLanguage;

        // Add event listener
        languageSelect.addEventListener('change', (e) => {
            currentLanguage = e.target.value;
            updateLanguageUI();
            loadFAQs(); // Reload FAQs in new language
        });
    }
}

// Update UI text based on selected language
function updateLanguageUI() {
    const messages = MESSAGES[currentLanguage];

    // Update placeholder
    chatInput.placeholder = messages.placeholder;

    // Update header
    const headerTitle = document.querySelector('.chat-header-content h3');
    const headerStatus = document.querySelector('.status-indicator');
    if (headerTitle) headerTitle.textContent = messages.headerTitle;
    if (headerStatus) headerStatus.textContent = messages.headerStatus;

    // Update initial message if it's the first message
    if (conversationHistory.length === 0) {
        const initialMessage = document.querySelector('.message.bot .message-content');
        if (initialMessage) {
            initialMessage.textContent = messages.initialGreeting;
        }
    }
}

// Set initial message time
function setInitialTime() {
    const timeElement = document.getElementById('initialTime');
    if (timeElement) {
        timeElement.textContent = getCurrentTime();
    }
}

// Get current time formatted
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
    });
}

// Setup Event Listeners
function setupEventListeners() {
    chatButton.addEventListener('click', toggleChat);
    closeButton.addEventListener('click', toggleChat);
    sendButton.addEventListener('click', sendMessage);
    stopButton.addEventListener('click', stopGeneration);
    voiceToggle.addEventListener('click', toggleVoice);
    micButton.addEventListener('click', toggleMicrophone);

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize input
    chatInput.addEventListener('input', () => {
        sendButton.disabled = chatInput.value.trim() === '';
    });

    // Initialize speech recognition
    initSpeechRecognition();
}

// Toggle chat widget
function toggleChat() {
    isOpen = !isOpen;
    chatWidget.classList.toggle('open');
    chatButton.classList.toggle('active');
    
    if (isOpen) {
        chatInput.focus();
        scrollToBottom();
    }
}

// Send message with API integration
async function sendMessage() {
    const message = chatInput.value.trim();

    if (message === '') return;

    // Add user message to chat
    addMessage(message, 'user');

    // Clear input
    chatInput.value = '';
    sendButton.disabled = true;

    // Use streaming or regular API
    if (USE_STREAMING) {
        await sendMessageStreaming(message);
    } else {
        await sendMessageRegular(message);
    }
}

// Regular non-streaming message
async function sendMessageRegular(message) {
    showTypingIndicator();

    try {
        const response = await fetchBotResponse(message);

        hideTypingIndicator();
        addMessage(response.answer, 'bot');

    } catch (error) {
        console.error('Error fetching response:', error);
        hideTypingIndicator();

        const messages = MESSAGES[currentLanguage];
        addMessage(messages.errorMessage, 'bot');
    }
}

// Streaming message with stop capability
async function sendMessageStreaming(message) {
    // Create abort controller for this request
    currentAbortController = new AbortController();

    // Show typing indicator while waiting for stream to start
    showTypingIndicator();

    // Show stop button
    showStopButton();

    try {
        const response = await fetchBotResponseStreaming(message, currentAbortController.signal);

    } catch (error) {
        hideTypingIndicator();
        if (error.name === 'AbortError') {
            console.log('Request was cancelled by user');
        } else {
            console.error('Error fetching response:', error);
            const messages = MESSAGES[currentLanguage];
            addMessage(messages.errorMessage, 'bot');
        }
    } finally {
        hideStopButton();
        currentAbortController = null;
        currentStreamingMessage = null;
    }
}

// Fetch response from backend API (regular, non-streaming)
async function fetchBotResponse(query) {
    const apiUrl = (typeof chatbotConfig !== 'undefined' && chatbotConfig.apiUrl)
        ? chatbotConfig.apiUrl
        : API_BASE_URL;

    try {
        const response = await fetch(`${apiUrl}${API_ENDPOINT}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                language: currentLanguage,
                top_k: 5,
                min_score: 0.3,
                style: 'standard',
                max_tokens: 512
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;

    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Fetch streaming response from backend API
async function fetchBotResponseStreaming(query, signal) {
    const apiUrl = (typeof chatbotConfig !== 'undefined' && chatbotConfig.apiUrl)
        ? chatbotConfig.apiUrl
        : API_BASE_URL;

    try {
        const response = await fetch(`${apiUrl}${STREAM_ENDPOINT}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                language: currentLanguage,
                top_k: 5,
                min_score: 0.3,
                style: 'standard',
                max_tokens: 512
            }),
            signal: signal  // Pass abort signal
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Process the stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullText = '';
        let messageDiv = null;
        let firstChunkReceived = false;

        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                break;
            }

            // Decode the chunk
            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE messages
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));

                    if (data.type === 'metadata') {
                        // Store metadata (sources, confidence, etc.)
                        console.log('Metadata:', data);
                    } else if (data.type === 'chunk') {
                        // Create message container on first chunk
                        if (!firstChunkReceived) {
                            hideTypingIndicator();
                            messageDiv = createStreamingMessage();
                            currentStreamingMessage = messageDiv;
                            firstChunkReceived = true;
                        }

                        // Append text chunk
                        fullText += data.text;
                        updateStreamingMessage(messageDiv, fullText);
                    } else if (data.type === 'done') {
                        // Stream complete
                        finalizeStreamingMessage(messageDiv, data.full_text);
                        console.log('Stream complete. Metrics:', data.metrics);
                    } else if (data.type === 'cancelled') {
                        // Stream was cancelled
                        finalizeStreamingMessage(messageDiv, data.partial_text || fullText, true);
                        console.log('Stream cancelled');
                    } else if (data.type === 'error') {
                        // Error occurred
                        throw new Error(data.error);
                    }
                }
            }
        }

    } catch (error) {
        hideTypingIndicator();
        if (currentStreamingMessage) {
            finalizeStreamingMessage(currentStreamingMessage, '', false, true);
        }
        throw error;
    }
}
// Comprehensive markdown to HTML converter
function markdownToHtml(text) {
    if (!text) return '';

    // First pass: Handle markdown links [text](url)
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color: #007bff; text-decoration: underline;">$1</a>');

    // Second pass: Handle bold text **text**
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Split into lines for processing
    const lines = text.split('\n');
    const output = [];
    let inList = false;
    let inParagraph = false;

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        const nextLine = i < lines.length - 1 ? lines[i + 1] : '';
        const isBlank = line.trim() === '';

        // Handle bullet points (•, -, or *)
        const bulletMatch = line.match(/^[\s]*[•\-\*]\s+(.+)$/);

        if (bulletMatch) {
            // Start list if needed
            if (!inList) {
                if (inParagraph) {
                    output.push('</p>');
                    inParagraph = false;
                }
                output.push('<ul>');
                inList = true;
            }

            // Process bold within list item
            const content = bulletMatch[1];
            output.push(`<li>${content}</li>`);

        } else if (isBlank) {
            // Blank line - close any open tags
            if (inList) {
                output.push('</ul>');
                inList = false;
            }
            if (inParagraph) {
                output.push('</p>');
                inParagraph = false;
            }

        } else {
            // Regular text line
            if (inList) {
                output.push('</ul>');
                inList = false;
            }

            // Check if next line is blank or bullet (paragraph boundary)
            const nextIsBlank = nextLine.trim() === '';
            const nextIsBullet = nextLine.match(/^[\s]*[•\-\*]\s+/);

            if (!inParagraph) {
                output.push('<p>');
                inParagraph = true;
            }

            output.push(line);

            // Add line break if not end of paragraph
            if (!nextIsBlank && !nextIsBullet && i < lines.length - 1) {
                output.push('<br>');
            }

            // Close paragraph at boundary
            if (nextIsBlank || nextIsBullet || i === lines.length - 1) {
                output.push('</p>');
                inParagraph = false;
            }
        }
    }

    // Close any remaining open tags
    if (inList) output.push('</ul>');
    if (inParagraph) output.push('</p>');

    return output.join('');
}

// Add message to chat
function addMessage(text, sender, sources = null, confidence = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const time = getCurrentTime();

    // Convert markdown to HTML for bot messages
    const formattedText = sender === 'bot' ? markdownToHtml(text) : escapeHtml(text);

    messageDiv.innerHTML = `
        <div class="message-content">${formattedText}</div>
        <div class="message-time">${time}</div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    // Store in conversation history
    conversationHistory.push({
        text: text,
        sender: sender,
        timestamp: new Date().toISOString()
    });
}

// Show typing indicator
function showTypingIndicator() {
    typingIndicator.classList.add('active');
    sendButton.disabled = true;
    chatInput.disabled = true;
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    typingIndicator.classList.remove('active');
    sendButton.disabled = false;
    chatInput.disabled = false;
}

// Scroll to bottom of messages
function scrollToBottom() {
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// Streaming Message Functions
// ============================================================================

// Create a new streaming message container
function createStreamingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot streaming';

    const time = getCurrentTime();

    messageDiv.innerHTML = `
        <div class="message-content"></div>
        <div class="message-time">${time}</div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    return messageDiv;
}

// Update streaming message with new text
function updateStreamingMessage(messageDiv, text) {
    const contentDiv = messageDiv.querySelector('.message-content');
    if (contentDiv) {
        const formattedText = markdownToHtml(text);
        contentDiv.innerHTML = formattedText;
        scrollToBottom();
    }
}

// Finalize streaming message (remove streaming class)
function finalizeStreamingMessage(messageDiv, text, wasCancelled = false, hasError = false) {
    messageDiv.classList.remove('streaming');

    const contentDiv = messageDiv.querySelector('.message-content');
    if (contentDiv) {
        if (hasError) {
            const messages = MESSAGES[currentLanguage];
            contentDiv.innerHTML = messages.errorMessage;
        } else if (text) {
            const formattedText = markdownToHtml(text);
            contentDiv.innerHTML = formattedText;

            // Add cancelled indicator if needed
            if (wasCancelled) {
                const cancelledNote = document.createElement('div');
                cancelledNote.style.cssText = 'font-size: 11px; color: #999; margin-top: 8px; font-style: italic;';
                cancelledNote.textContent = currentLanguage === 'DE' ? '(Abgebrochen)' :
                                           currentLanguage === 'FR' ? '(Annulé)' :
                                           '(Stopped)';
                contentDiv.appendChild(cancelledNote);
            }
        }
    }

    scrollToBottom();

    // Store in conversation history
    conversationHistory.push({
        text: text,
        sender: 'bot',
        timestamp: new Date().toISOString(),
        wasCancelled: wasCancelled
    });
}

// ============================================================================
// Stop Button Functions
// ============================================================================

// Show stop button
function showStopButton() {
    if (stopButton) {
        console.log('Showing stop button');
        stopButton.classList.add('visible');
        sendButton.classList.add('hidden');
    } else {
        console.error('Stop button element not found!');
    }
}

// Hide stop button
function hideStopButton() {
    if (stopButton) {
        stopButton.classList.remove('visible');
        sendButton.classList.remove('hidden');
    }
}

// Stop the current generation
function stopGeneration() {
    if (currentAbortController) {
        console.log('Stopping generation...');
        currentAbortController.abort();
        hideStopButton();
    }
}

// ============================================================================
// FAQ Functions
// ============================================================================

// Load all FAQs from hardcoded data (instant, no API call)
function loadFAQs() {
    // Copy hardcoded FAQ data to cache
    faqCache = { ...HARDCODED_FAQS };

    // Update button texts based on current language
    updateFAQButtonTexts();

    console.log(`Loaded ${Object.keys(faqCache).length} FAQs (hardcoded, instant)`);
}

// Update FAQ button texts based on current language
function updateFAQButtonTexts() {
    const faqButtons = document.querySelectorAll('.faq-button');

    faqButtons.forEach(button => {
        const faqId = button.getAttribute('data-faq-id');
        const faq = faqCache[faqId];

        if (faq && faq.question && faq.question[currentLanguage]) {
            button.textContent = faq.question[currentLanguage];
        }
    });

    // Update FAQ title based on language
    const faqTitle = document.querySelector('.faq-title');
    if (faqTitle) {
        const titles = {
            DE: 'Häufig gestellte Fragen:',
            EN: 'Frequently Asked Questions:',
            FR: 'Questions fréquemment posées:'
        };
        faqTitle.textContent = titles[currentLanguage] || titles.EN;
    }
}

// Setup FAQ button click handlers
function setupFAQButtons() {
    const faqButtons = document.querySelectorAll('.faq-button');

    faqButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const faqId = button.getAttribute('data-faq-id');
            await handleFAQClick(faqId);
        });
    });
}

// Handle FAQ button click - instant response from hardcoded data
function handleFAQClick(faqId) {
    // Get FAQ from hardcoded cache (always available, instant response)
    const faq = faqCache[faqId];

    if (!faq) {
        console.error(`FAQ not found: ${faqId}`);
        const messages = MESSAGES[currentLanguage];
        addMessage(messages.errorMessage, 'bot');
        return;
    }

    // Get question and answer in current language
    const question = faq.question[currentLanguage];
    const answer = faq.answer[currentLanguage];

    // Validate language-specific content exists
    if (!question || !answer) {
        console.error(`FAQ ${faqId} missing translation for ${currentLanguage}`);
        const messages = MESSAGES[currentLanguage];
        addMessage(messages.errorMessage, 'bot');
        return;
    }

    // Display question as user message
    addMessage(question, 'user');

    // Display answer as bot message (instant response)
    setTimeout(() => {
        addMessage(answer, 'bot');
        // Don't hide FAQs - keep them visible like inspiration widget
    }, 100); // Small delay for UX (feels more natural)
}

// Hide FAQ buttons after first interaction
function hideFAQs() {
    if (!faqsHidden) {
        const faqSection = document.getElementById('faqSection');
        if (faqSection) {
            faqSection.classList.add('hidden');
            faqsHidden = true;
        }
    }
}

// Show FAQ buttons again (optional - for reset)
function showFAQs() {
    const faqSection = document.getElementById('faqSection');
    if (faqSection) {
        faqSection.classList.remove('hidden');
        faqsHidden = false;
    }
}

// ============================================================================
// Voice and Speech Recognition Functions
// ============================================================================

// Get last bot message from conversation history
function getLastBotMessage() {
    for (let i = conversationHistory.length - 1; i >= 0; i--) {
        const msg = conversationHistory[i];
        if (msg.sender === 'bot' && msg.text && !msg.wasCancelled) {
            return msg.text;
        }
    }
    return null;
}

// Strip markdown formatting for TTS (keeps text clean for audio)
function stripMarkdownForTTS(text) {
    if (!text) return text;

    let cleaned = text;

    // Remove bold: **text** or __text__
    cleaned = cleaned.replace(/\*\*(.+?)\*\*/g, '$1');
    cleaned = cleaned.replace(/__(.+?)__/g, '$1');

    // Remove italic: *text* or _text_ (but not in URLs or already processed)
    cleaned = cleaned.replace(/\*(.+?)\*/g, '$1');
    cleaned = cleaned.replace(/\b_(.+?)_\b/g, '$1');

    // Remove links: [text](url) → text
    cleaned = cleaned.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');

    // Remove headers: ## Header → Header
    cleaned = cleaned.replace(/^#{1,6}\s+/gm, '');

    // Remove list markers: • item, - item, * item → item
    cleaned = cleaned.replace(/^[\s]*[•\-\*]\s+/gm, '');

    // Remove inline code: `code` → code
    cleaned = cleaned.replace(/`([^`]+)`/g, '$1');

    // Remove code blocks: ```code``` → code
    cleaned = cleaned.replace(/```[\s\S]*?```/g, (match) => {
        return match.replace(/```/g, '').trim();
    });

    // Clean up multiple spaces
    cleaned = cleaned.replace(/\s+/g, ' ').trim();

    return cleaned;
}

// Generate and play TTS audio
async function speakText(text, language) {
    try {
        showSpeakingAnimation();

        // Clean up previous audio
        stopAudio();

        // Strip markdown formatting for clean audio
        const cleanText = stripMarkdownForTTS(text);

        console.log(`Generating TTS for: "${cleanText.substring(0, 50)}..." (${language})`);

        // Call TTS API
        const response = await fetch(`${API_BASE_URL}/api/v1/tts/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: cleanText,
                language: language
            })
        });

        if (!response.ok) {
            throw new Error(`TTS API error: ${response.status}`);
        }

        const data = await response.json();
        console.log('TTS generated:', data);

        // Fetch audio file
        const audioUrl = `${API_BASE_URL}${data.audio_url}`;
        const audioResponse = await fetch(audioUrl);

        if (!audioResponse.ok) {
            throw new Error(`Failed to fetch audio: ${audioResponse.status}`);
        }

        const audioBlob = await audioResponse.blob();
        currentAudioBlob = URL.createObjectURL(audioBlob);

        // Create and play audio
        currentAudio = new Audio(currentAudioBlob);

        // Event handlers
        currentAudio.addEventListener('play', () => {
            console.log('Audio playback started');
            showSpeakingAnimation();
        });

        currentAudio.addEventListener('ended', () => {
            console.log('Audio playback finished');
            hideSpeakingAnimation();
            cleanupAudioBlob();
        });

        currentAudio.addEventListener('error', (e) => {
            console.error('Audio playback error:', e);
            hideSpeakingAnimation();
            cleanupAudioBlob();
        });

        // Start playback
        await currentAudio.play();

    } catch (error) {
        console.error('TTS error:', error);
        hideSpeakingAnimation();
        // Show error message
        const messages = MESSAGES[currentLanguage];
        if (messages && messages.ttsError) {
            // Optionally show error notification to user
            console.warn(messages.ttsError);
        }
    }
}

// Stop current audio playback
function stopAudio() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio = null;
    }
    cleanupAudioBlob();
    hideSpeakingAnimation();
}

// Clean up blob URL to prevent memory leaks
function cleanupAudioBlob() {
    if (currentAudioBlob) {
        // Add to cache instead of immediate cleanup
        const cacheEntry = {
            url: currentAudioBlob,
            timestamp: Date.now(),
            timeout: setTimeout(() => {
                URL.revokeObjectURL(currentAudioBlob);
                // Remove from cache array
                const index = audioCache.indexOf(cacheEntry);
                if (index > -1) {
                    audioCache.splice(index, 1);
                }
            }, AUDIO_TTL)
        };

        audioCache.push(cacheEntry);

        // Keep only last 3 - remove oldest if exceeded
        if (audioCache.length > MAX_AUDIO_CACHE_SIZE) {
            const oldest = audioCache.shift();
            clearTimeout(oldest.timeout);
            URL.revokeObjectURL(oldest.url);
        }

        currentAudioBlob = null;
    }
}

// Toggle voice output and play last bot message
async function toggleVoice() {
    isVoiceEnabled = !isVoiceEnabled;

    if (isVoiceEnabled) {
        voiceToggle.classList.add('active');

        // Get last bot message
        const lastBotMessage = getLastBotMessage();
        if (lastBotMessage) {
            await speakText(lastBotMessage, currentLanguage);
        } else {
            console.warn('No bot message to read');
        }
    } else {
        // Stop current playback
        stopAudio();
        voiceToggle.classList.remove('active');
        voiceToggle.classList.remove('speaking');
        voiceToggle.classList.add('muted');
        if (pitchAnimation) {
            pitchAnimation.style.display = 'none';
        }
        setTimeout(() => voiceToggle.classList.remove('muted'), 300);
    }

    console.log('Voice output:', isVoiceEnabled ? 'enabled' : 'disabled');
}

// Show speaking animation
function showSpeakingAnimation() {
    if (isVoiceEnabled && voiceToggle && pitchAnimation) {
        voiceToggle.classList.add('speaking');
        pitchAnimation.style.display = 'flex';
    }
}

// Hide speaking animation
function hideSpeakingAnimation() {
    if (voiceToggle && pitchAnimation) {
        voiceToggle.classList.remove('speaking');
        pitchAnimation.style.display = 'none';
    }
}

// Initialize speech recognition
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.log('Speech recognition not supported');
        micButton.style.display = 'none';
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US'; // Can be changed based on currentLanguage

    recognition.onstart = () => {
        isListening = true;
        micButton.classList.add('listening');
        console.log('Speech recognition started');
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        chatInput.value = transcript;
        sendButton.disabled = false;

        // Auto-send after a short delay
        setTimeout(() => {
            if (transcript.trim()) {
                sendMessage();
            }
        }, 500);
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isListening = false;
        micButton.classList.remove('listening');

        if (event.error === 'no-speech') {
            alert('No speech detected. Please try again.');
        } else if (event.error === 'not-allowed') {
            alert('Microphone permission denied. Please enable it in your browser settings.');
        }
    };

    recognition.onend = () => {
        isListening = false;
        micButton.classList.remove('listening');
        console.log('Speech recognition ended');
    };
}

// Toggle microphone for speech input
function toggleMicrophone() {
    if (!recognition) {
        alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
        return;
    }

    if (isListening) {
        recognition.stop();
    } else {
        try {
            recognition.start();
        } catch (error) {
            console.error('Error starting speech recognition:', error);
        }
    }
}

// Initialize the chatbot
init();