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
let userHasScrolled = false; // Track if user has manually scrolled up during streaming
let lastScrollTop = 0; // Track last scroll position to detect user scroll
let scrollPending = false; // Throttle scroll updates

// Audio player state for TTS
let currentAudio = null;  // HTML5 Audio instance
let currentAudioBlob = null;  // Blob URL for cleanup
let audioCache = [];  // Store last 3 audio blobs with TTL
const MAX_AUDIO_CACHE_SIZE = 3;
const AUDIO_TTL = 5 * 60 * 1000; // 5 minutes in milliseconds

// Configuration
const API_BASE_URL = 'http://3.79.17.125';  // Deployed backend URL
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
            EN: "How to contact you?",
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
    },
    orthopedics: {
        id: "orthopedics",
        question: {
            EN: "What does your orthopedics department treat?",
            DE: "Was behandelt die Orthopädie bei functiomed?",
            FR: "Que traite le département d'orthopédie de functiomed ?"
        },
        answer: {
            EN: "Orthopedics at functiomed deals with diseases and injuries of the **musculoskeletal system**, including **bones**, **joints**, **muscles**, and **tendons**.",
            DE: "Die Orthopädie bei functiomed befasst sich mit Erkrankungen und Verletzungen des **Bewegungsapparates**, einschließlich **Knochen**, **Gelenken**, **Muskeln** und **Sehnen**.",
            FR: "L'orthopédie chez functiomed s'occupe des maladies et des blessures de l'**appareil locomoteur**, y compris les **os**, les **articulations**, les **muscles** et les **tendons**."
        },
        category: "services"
    },
    orthopedics_functiomed: {
        id: "orthopedics_functiomed",
        question: {
            EN: "What does the orthopedics department at functiomed treat?",
            DE: "Was behandelt die Orthopädie-Abteilung bei functiomed?",
            FR: "Que traite le département d'orthopédie chez functiomed ?"
        },
        answer: {
            EN: "Our orthopedics team helps with conditions that affect the **musculoskeletal system**. This includes problems involving **bones, joints, muscles, and tendons**, whether they are caused by injuries or chronic issues.",
            DE: "Unser Orthopädie-Team hilft bei Erkrankungen, die das **Bewegungsapparates** betreffen. Dazu gehören Probleme mit **Knochen, Gelenken, Muskeln und Sehnen**, egal ob sie durch Verletzungen oder chronische Beschwerden verursacht werden.",
            FR: "Notre équipe d'orthopédie aide à traiter les affections qui touchent l'**appareil locomoteur**. Cela inclut les problèmes concernant les **os, articulations, muscles et tendons**, qu'ils soient causés par des blessures ou des problèmes chroniques."
        },
        category: "services"
    },
    osteopathy_suitable: {
        id: "osteopathy_suitable",
        question: {
            EN: "For whom is osteopathic treatment suitable for?",
            DE: "Für wen ist eine osteopathische Behandlung geeignet?",
            FR: "Pour qui le traitement ostéopathique est-il adapté ?"
        },
        answer: {
            EN: "Osteopathy is suitable for people of **all ages**, from newborn babies to elderly patients. ",
            DE: "Osteopathie ist für Menschen **jeden Alters** geeignet, von neugeborenen Babys bis zu älteren Patienten.",
            FR: "L'ostéopathie convient aux personnes de **tout âge**, des nouveau-nés aux patients âgés."
        },
        category: "services"
    },
    rheumatology: {
        id: "rheumatology",
        question: {
            EN: "Which conditions does rheumatology treat?",
            DE: "Welche Erkrankungen behandelt die Rheumatologie?",
            FR: "Quelles maladies sont traitées par le service de rhumatologie ?"
        },
        answer: {
            EN: "Our rheumatology department specializes in the diagnosis and treatment of a wide range of rheumatic conditions.",
            DE: "Unsere Rheumatologie-Abteilung ist auf die Diagnose und Behandlung einer Vielzahl rheumatischer Erkrankungen spezialisiert.",
            FR: "Notre service de rhumatologie est spécialisé dans le diagnostic et le traitement d'un large éventail de conditions rhumatismales."
        },
        category: "services"
    },
    integrative_medicine: {
        id: "integrative_medicine",
        question: {
            EN: "What is integrative medicine?",
            DE: "Was versteht man unter integrativer Medizin?",
            FR: "Que signifie la médecine intégrative ?"
        },
        answer: {
            EN: "Integrative medicine combines **conventional medical treatments** with **complementary therapies** for a holistic approach.",
            DE: "Integrative Medizin kombiniert schulmedizinische Verfahren** mit **komplementären Therapien** für eine ganzheitliche Behandlung.",
            FR: "La médecine intégrative combine les **traitements médicaux conventionnels** avec des **thérapies complémentaires** pour une prise en charge globale."
        },
        category: "services"
    },
    integrative_medicine_meaning: {
        id: "integrative_medicine_meaning",
        question: {
            EN: "What is meant by integrative medicine?",
            DE: "Was ist mit integrativer Medizin gemeint?",
            FR: "Que signifie par médecine intégrative ?"
        },
        answer: {
            EN: "Integrative medicine combines **conventional medical treatments** with **complementary therapies** for a holistic approach.",
            DE: "Integrative Medizin kombiniert schulmedizinische Verfahren** mit **komplementären Therapien** für eine ganzheitliche Behandlung.",
            FR: "La médecine intégrative combine les **traitements médicaux conventionnels** avec des **thérapies complémentaires** pour une prise en charge globale."
        },
        category: "services"
    },
    complementary_medicine: {
        id: "complementary_medicine",
        question: {
            EN: "What does complementary medicine include?",
            DE: "Was umfasst die Komplementärmedizin bei functiomed?",
            FR: "Que comprend la médecine complémentaire chez functiomed ?"
        },
        answer: {
            EN: "Our complementary medicine includes **acupuncture**, **homeopathy**, **medical massages**, and other alternative healing methods.",
            DE: "Unsere Komplementärmedizin umfasst **Akupunktur**, **Homöopathie**, **medizinische Massagen** und andere alternative Heilmethoden.",
            FR: "Notre médecine complémentaire comprend **l'acupuncture**, **l'homéopathie**, les **massages thérapeutiques** et d'autres méthodes de guérison alternatives."
        },
        category: "services"
    },
    complementary_medicine_functiomed: {
        id: "complementary_medicine_functiomed",
        question: {
            EN: "What does complementary medicine at functiomed include?",
            DE: "Was umfasst die Komplementärmedizin bei functiomed?",
            FR: "Que comprend la médecine complémentaire chez functiomed ?"
        },
        answer: {
            EN: "Our complementary medicine includes **acupuncture**, **homeopathy**, **medical massages**, and other alternative healing methods.",
            DE: "Unsere Komplementärmedizin umfasst **Akupunktur**, **Homöopathie**, **medizinische Massagen** und andere alternative Heilmethoden.",
            FR: "Notre médecine complémentaire comprend **l'acupuncture**, **l'homéopathie**, les **massages thérapeutiques** et d'autres méthodes de guérison alternatives."
        },
        category: "services"
    },
    parking: {
        id: "parking",
        question: {
            EN: "Are there parking facilities at functiomed?",
            DE: "Gibt es Parkmöglichkeiten bei functiomed?",
            FR: "Y a-t-il des places de parking chez functiomed ?"
        },
        answer: {
            EN: "**Yes**, you'll find **free parking spaces** right in front of our practice, and there are also public parking options in the nearby area.",
            DE: "**Ja**, Sie finden **kostenlose Parkplätze** direkt vor unserer Praxis, und es gibt auch öffentliche Parkmöglichkeiten in der Nähe.",
            FR: "**Oui**, vous trouverez des **places de parking gratuites** juste devant notre cabinet, et il y a également des options de stationnement public dans les environs."
        },
        category: "general"
    },
    languages: {
        id: "languages",
        question: {
            EN: "Which languages do the staff speak?",
            DE: "Welche Sprachen sprechen die Mitarbeitenden?",
            FR: "Quelles langues le personnel parle-t-il ?"
        },
        answer: {
            EN: "Our team speaks **German, English, French, Italian**, and several other languages. Just let us know your preferred language so we can make your visit as comfortable as possible.",
            DE: "Unser Team spricht **Deutsch, Englisch, Französisch, Italienisch** und mehrere andere Sprachen. Teilen Sie uns einfach Ihre bevorzugte Sprache mit, damit wir Ihren Besuch so angenehm wie möglich gestalten können.",
            FR: "Notre équipe parle **allemand, anglais, français, italien** et plusieurs autres langues. Faites-nous simplement savoir votre langue préférée afin que nous puissions rendre votre visite aussi confortable que possible."
        },
        category: "general"
    },
    sports_medicine: {
        id: "sports_medicine",
        question: {
            EN: "What services does sports medicine offer?",
            DE: "Welche Leistungen bietet die Sportmedizin?",
            FR: "Quels services offre la médecine du sport ?"
        },
        answer: {
            EN: "We provide comprehensive support for athletes, from **preventing** injuries to **diagnosing** and **treating** sports-related problems. We're here for both **recreational** and **professional** athletes.",
            DE: "Wir bieten umfassende Unterstützung für Sportler, von der **Prävention** von Verletzungen bis zur **Diagnose** und **Behandlung** sportbedingter Probleme. Wir sind für **Freizeit-** und **Profisportler** da.",
            FR: "Nous offrons un soutien complet aux athlètes, de la **prévention** des blessures au **diagnostic** et au **traitement** des problèmes liés au sport. Nous sommes là pour les athlètes **amateurs** et **professionnels**."
        },
        category: "medical"
    },
    referral: {
        id: "referral",
        question: {
            EN: "Do I need a referral for an appointment?",
            DE: "Benötige ich eine Überweisung für einen Termin?",
            FR: "Ai-je besoin d'une ordonnance pour un rendez-vous ?"
        },
        answer: {
            EN: "**Not necessarily**. You can book an appointment directly with us unless you're part of a special insurance model, such as the primary care physician model, which may require a referral.",
            DE: "**Nicht unbedingt**. Sie können direkt einen Termin bei uns buchen, es sei denn, Sie sind Teil eines speziellen Versicherungsmodells, wie z.B. das Hausarztmodell, das möglicherweise eine Überweisung erfordert.",
            FR: "**Pas nécessairement**. Vous pouvez prendre rendez-vous directement avec nous sauf si vous faites partie d'un modèle d'assurance spécial, tel que le modèle de médecin de famille, qui peut nécessiter une ordonnance."
        },
        category: "general"
    },
    insurance_coverage: {
        id: "insurance_coverage",
        question: {
            EN: "Are the costs covered by health insurance?",
            DE: "Werden die Kosten von der Krankenkasse übernommen?",
            FR: "Les coûts sont-ils couverts par l'assurance maladie ?"
        },
        answer: {
            EN: "Most orthopedic and traumatology treatments are covered by **basic** health insurance or **accident** insurance. We always recommend checking with your insurance provider in advance to understand exactly what is covered for your specific situation.",
            DE: "Die meisten orthopädischen und traumatologischen Behandlungen werden von der **Grundversicherung** oder **Unfallversicherung** übernommen. Wir empfehlen immer, vorab bei Ihrer Versicherung nachzufragen, um genau zu verstehen, was für Ihre spezifische Situation abgedeckt ist.",
            FR: "La plupart des traitements orthopédiques et traumatologiques sont couverts par **l'assurance de base** ou **l'assurance accident**. Nous recommandons toujours de vérifier auprès de votre assureur à l'avance pour comprendre exactement ce qui est couvert pour votre situation spécifique."
        },
        category: "general"
    },
    osteopathy_sessions: {
        id: "osteopathy_sessions",
        question: {
            EN: "How many sessions are necessary?",
            DE: "Wie viele Sitzungen sind notwendig?",
            FR: "Combien de séances sont nécessaires ?"
        },
        answer: {
            EN: "This depends on your individual situation. Many patients benefit from several sessions, but the exact number varies from case to case.",
            DE: "Das hängt von Ihrer individuellen Situation ab. Viele Patienten profitieren von mehreren Sitzungen, aber die genaue Anzahl variiert von Fall zu Fall.",
            FR: "Cela dépend de votre situation individuelle. De nombreux patients bénéficient de plusieurs séances, mais le nombre exact varie d'un cas à l'autre."
        },
        category: "medical"
    },
    osteopathy_insurance: {
        id: "osteopathy_insurance",
        question: {
            EN: "Is osteopathy covered by health insurance?",
            DE: "Wird Osteopathie von der Krankenkasse bezahlt?",
            FR: "L'ostéopathie est-elle couverte par l'assurance maladie ?"
        },
        answer: {
            EN: "**Supplementary insurance** often covers **part of the costs**. It's always best for patients to check their coverage in advance.",
            DE: "**Zusatzversicherungen** übernehmen oft einen **Teil der Kosten**. Es ist immer am besten, wenn Patienten ihre Deckung im Voraus prüfen.",
            FR: "**L'assurance complémentaire** couvre souvent une **partie des coûts**. Il est toujours préférable que les patients vérifient leur couverture à l'avance."
        },
        category: "insurance"
    },
    internal_medicine: {
        id: "internal_medicine",
        question: {
            EN: "What does internal medicine at functiomed include?",
            DE: "Was umfasst die Innere Medizin bei functiomed?",
            FR: "Que comprend la médecine interne chez functiomed ?"
        },
        answer: {
            EN: "Internal medicine at functiomed focuses on the prevention, diagnosis, and treatment of diseases affecting the body's **internal organs**. This includes conditions related to the **heart, lungs, liver, kidneys**, and other vital systems. Our specialists take a comprehensive approach, considering the overall health of each patient, to provide accurate diagnoses, effective treatment plans, and ongoing care for both acute and chronic medical conditions.",
            DE: "Die Innere Medizin bei functiomed konzentriert sich auf die Prävention, Diagnose und Behandlung von Erkrankungen, die die **inneren Organe** des Körpers betreffen. Dazu gehören Erkrankungen im Zusammenhang mit **Herz, Lunge, Leber, Nieren** und anderen lebenswichtigen Systemen. Unsere Spezialisten verfolgen einen umfassenden Ansatz und berücksichtigen die allgemeine Gesundheit jedes Patienten, um genaue Diagnosen, wirksame Behandlungspläne und kontinuierliche Betreuung sowohl für akute als auch chronische Erkrankungen bereitzustellen.",
            FR: "La médecine interne chez functiomed se concentre sur la prévention, le diagnostic et le traitement des maladies affectant les **organes internes** du corps. Cela inclut les conditions liées au **cœur, poumons, foie, reins** et autres systèmes vitaux. Nos spécialistes adoptent une approche globale, en tenant compte de la santé générale de chaque patient, pour fournir des diagnostics précis, des plans de traitement efficaces et des soins continus pour les affections médicales aiguës et chroniques."
        },
        category: "medical"
    },
    diagnosis: {
        id: "diagnosis",
        question: {
            EN: "How is the diagnosis made?",
            DE: "Wie erfolgt die Diagnosestellung?",
            FR: "Comment est posée la diagnosis ?"
        },
        answer: {
            EN: "We use a combination of **laboratory tests** and modern **imaging techniques** to ensure an accurate diagnosis.",
            DE:  "Wir verwenden eine Kombination aus **Labortests** und modernen **Bildgebungsverfahren**, um eine genaue Diagnose zu gewährleisten.",
            FR: "Nous utilisons une combinaison d'**analyses de laboratoire** et de **techniques d'imagerie modernes** pour assurer un diagnostic précis."
        },
        category: "medical"
    },
    fasting: {
        id: "fasting",
        question: {
            EN: "Do I need to fast for a blood test?",
            DE: "Muss ich nüchtern zur Blutabnahme erscheinen?",
            FR: "Dois-je jeûner pour une prise de sang ?"
        },
        answer: {
            EN: "For certain blood tests, fasting is required. We will inform you in advance.",
            DE: "Einige Bluttests erfordern Fasten. Keine Sorge, wir informieren Sie im Voraus, falls dies auf Sie zutrifft.",
            FR: "Certains tests sanguins nécessitent le jeûne. Ne vous inquiétez pas, nous vous informerons à l'avance si cela s'applique à vous."
        },
        category: "medical"
    },
    therapies: {
        id: "therapies",
        question: {
            EN: "Which therapies are offered?",
            DE: "Welche Therapien werden angeboten?",
            FR: "Quelles thérapies sont proposées ?"
        },
        answer: {
            EN: "Within our integrative medicine program, we offer a wide range of therapies designed to complement conventional medical treatments. These include **acupuncture, homeopathy, infusion therapies, colon hydrotherapy, ozone therapy, orthomolecular medicine, nutritional counseling**, and **mental coaching**. Each therapy is carefully selected to support your overall health, promote healing, and enhance your quality of life, with treatment plans tailored to your individual needs.",
            DE: "Im Rahmen unseres Programms für integrative Medizin bieten wir eine Vielzahl von Therapien an, die die konventionelle medizinische Behandlung ergänzen. Dazu gehören **Akupunktur, Homöopathie, Infusionstherapien, Colon-Hydro-Therapie, Ozontherapie, Orthomolekularmedizin, Ernährungsberatung** und **Mental Coaching**. Jede Therapie wird sorgfältig ausgewählt, um Ihre allgemeine Gesundheit zu unterstützen, die Heilung zu fördern und Ihre Lebensqualität zu verbessern, wobei die Behandlungspläne auf Ihre individuellen Bedürfnisse zugeschnitten sind.",
            FR: "Dans le cadre de notre programme de médecine intégrative, nous proposons une large gamme de thérapies conçues pour compléter les traitements médicaux conventionnels. Celles-ci incluent **l'acupuncture, l'homéopathie, les thérapies par perfusion, l'hydrothérapie du côlon, la thérapie par ozone, la médecine orthomoléculaire, le conseil nutritionnel** et **le coaching mental**. Chaque thérapie est soigneusement sélectionnée pour soutenir votre santé globale, favoriser la guérison et améliorer votre qualité de vie, avec des plans de traitement adaptés à vos besoins individuels."
        },
        category: "medical"
    },
    integrative_science: {
        id: "integrative_science",
        question: {
            EN: "Is integrative medicine scientifically recognized?",
            DE: "Ist integrative Medizin wissenschaftlich anerkannt?",
            FR: "La médecine intégrative est-elle scientifiquement reconnue ?"
        },
        answer: {
            EN: "Many of the methods we use have been scientifically examined and work well alongside conventional medicine.",
            DE: "Viele der von uns angewandten Methoden wurden wissenschaftlich untersucht und ergänzen die Schulmedizin sehr gut.",
            FR: "De nombreuses méthodes que nous utilisons ont été examinées scientifiquement et fonctionnent bien en complément de la médecine conventionnelle."
        },
        category: "medical"
    },
    therapy_selection: {
        id: "therapy_selection",
        question: {
            EN: "How do I find the right therapy for me?",
            DE: "Wie finde ich die passende Therapie für mich?",
            FR: "Comment trouver la thérapie qui me convient ?"
        },
    answer: {
        EN: "Choosing the right therapy depends on your individual health needs, goals, and preferences. During a **personal consultation**, our specialists will review your medical history, discuss your symptoms, and assess your overall condition. Based on this information, we will recommend the most suitable treatment options and create a tailored plan to help you achieve the best possible results for your health and well-being.",
        DE: "Die Wahl der richtigen Therapie hängt von Ihren individuellen Gesundheitsbedürfnissen, Zielen und Vorlieben ab. In einem **persönlichen Gespräch** prüfen unsere Spezialisten Ihre Krankengeschichte, besprechen Ihre Symptome und beurteilen Ihren allgemeinen Zustand. Auf dieser Grundlage empfehlen wir die am besten geeigneten Behandlungsmöglichkeiten und erstellen einen individuell zugeschnittenen Plan, um die bestmöglichen Ergebnisse für Ihre Gesundheit und Ihr Wohlbefinden zu erzielen.",
        FR: "Le choix de la thérapie appropriée dépend de vos besoins de santé, de vos objectifs et de vos préférences individuels. Lors d'une **consultation personnelle**, nos spécialistes examineront vos antécédents médicaux, discuteront de vos symptômes et évalueront votre état général. Sur cette base, nous recommanderons les options de traitement les plus adaptées et créerons un plan personnalisé pour vous aider à obtenir les meilleurs résultats possibles pour votre santé et votre bien-être."
    },
        category: "medical"
    },
    acupuncture: {
        id: "acupuncture",
        question: {
            EN: "How does an acupuncture session work?",
            DE: "Wie läuft eine Akupunktursitzung ab?",
            FR: "Comment se déroule une séance d'acupuncture ?"
        },
    answer: {
        EN: "During an acupuncture session, **very fine needles** are carefully placed at **specific points** on the body to help balance energy flow and support the body’s natural healing processes. \nFor children or anyone who is uncomfortable with needles but still wants to benefit from Far Eastern healing methods, we offer Tuina. **Tuina** is a traditional Chinese massage technique that uses gentle manual movements to **improve energy flow, release blockages**, and promote harmony between body and mind. Each session is tailored to the individual’s needs to ensure a safe and effective treatment.",
        DE: "Während einer Akupunktursitzung werden **sehr feine Nadeln** sorgfältig an **spezifischen Punkten** des Körpers gesetzt, um den Energiefluss zu harmonisieren und die natürlichen Heilungsprozesse des Körpers zu unterstützen. \nFür Kinder oder alle, die sich mit Nadeln unwohl fühlen, aber dennoch von fernöstlichen Heilmethoden profitieren möchten, bieten wir Tuina an. **Tuina** ist eine traditionelle chinesische Massagetechnik, bei der sanfte manuelle Bewegungen den **Energiefluss verbessern, Blockaden lösen** und Harmonie zwischen Körper und Geist fördern. Jede Sitzung wird individuell angepasst, um eine sichere und effektive Behandlung zu gewährleisten.",
        FR: "Lors d'une séance d'acupuncture, des **aiguilles très fines** sont placées avec soin à des **points spécifiques** du corps pour aider à équilibrer le flux d'énergie et soutenir les processus naturels de guérison. \nPour les enfants ou toute personne mal à l'aise avec les aiguilles mais souhaitant bénéficier des méthodes de guérison de l'Extrême-Orient, nous proposons le Tuina. **Tuina** est une technique de massage chinoise traditionnelle utilisant des mouvements manuels doux pour **améliorer le flux d'énergie, libérer les blocages** et promouvoir l'harmonie entre le corps et l'esprit. Chaque séance est adaptée aux besoins individuels pour garantir un traitement sûr et efficace."
    },
        category: "medical"
    },
    homeopathy: {
        id: "homeopathy",
        question: {
            EN: "Is homeopathy suitable for children?",
            DE: "Ist Homöopathie für Kinder geeignet?",
            FR: "L'homéopathie est-elle adaptée aux enfants ?"
        },
    answer: {
        EN: "**Yes**, homeopathy is **safe and suitable** for children of all ages. Treatments are completely needle-free and gentle, making them well-tolerated by young patients. Homeopathy can help support a child’s natural healing processes, address common ailments, and improve overall well-being, all while being adapted to the individual needs of each child.",
        DE: "**Ja**, Homöopathie ist **sicher und für Kinder jeden Alters geeignet**. Die Behandlungen sind vollständig nadelfrei und sanft, sodass sie von jungen Patienten gut vertragen werden. Homöopathie kann die natürlichen Heilungsprozesse eines Kindes unterstützen, häufige Beschwerden lindern und das allgemeine Wohlbefinden verbessern, wobei sie stets an die individuellen Bedürfnisse des Kindes angepasst wird.",
        FR: "**Oui**, l'homéopathie est **sans danger et adaptée** aux enfants de tout âge. Les traitements sont totalement sans aiguilles et doux, ce qui les rend bien tolérés par les jeunes patients. L'homéopathie peut soutenir les processus naturels de guérison de l'enfant, traiter les affections courantes et améliorer le bien-être général, tout en étant adaptée aux besoins individuels de chaque enfant."
    },
        category: "medical"
    },
    massage: {
        id: "massage",
        question: {
            EN: "Which massage techniques are offered?",
            DE: "Welche Massagetechniken werden angeboten?",
            FR: "Quelles techniques de massage sont proposées ?"
        },
        answer: {
            EN: "We offer **classic** massages, **reflexology**, **hot stone** massages, **Japanese facial** massage, **Lomi Lomi**, **pregnancy** massage, **anti-cellulite** massage, **manual lymphatic drainage**, **Shiatsu**, and **sports** massages.",
            DE: "Wir bieten **klassische** Massagen, **Fußreflexzonenmassagen**, **Hot-Stone-Massagen**, **Japanische Gesichtsmassage**, **Lomi Lomi**, **Schwangerschaftsmassage**, **Anti Cellulite Massage**, **Manuelle Lymphdrainage**, **Shiatsu** und **Sportmassagen** an.",
            FR: "Nous proposons des **massages classiques**, des **massages réflexes**, des **massages aux pierres chaudes**, le **massage facial japonais**, le **Lomi Lomi**, les **massages prénataux**, le **massage anti-cellulite**, le **drainage lymphatique manuel**, le **Shiatsu** et les **massages sportifs**."
        },
        category: "medical"
    },
    hours_practice: {
        id: "hours_practice",
        question: {
            EN: "What are the practice opening hours?",
            DE: "Wie sind die Öffnungszeiten der Praxis?",
            FR: "Quels sont les horaires d'ouverture de la pratique ?"
        },
        answer: {
            EN: "Our regular opening hours are **Monday to Friday, from 08:00 to 18:00**. Appointments outside these hours are possible by arrangement.",
            DE: "Unsere regulären Öffnungszeiten sind **Montag bis Freitag, von 08:00 bis 18:00 Uhr**. Termine außerhalb dieser Zeiten sind nach Vereinbarung möglich.",
            FR: "Nos heures d'ouverture régulières sont du **lundi au vendredi, de 08h00 à 18h00**. Des rendez-vous en dehors de ces heures sont possibles sur arrangement."
        },
        category: "general"
    },
    appointment_booking: {
        id: "appointment_booking",
        question: {
            EN: "How can I make an appointment?",
            DE: "Wie kann ich einen Termin vereinbaren?",
            FR: "Comment puis-je prendre rendez-vous ?"
        },
        answer: {
            EN: "**Booking link:** [Click here to book online](https://functiomed.thefotoloft.ch/pages/online-termin-buchen/)\n\n**Step-by-Step Guide:**\n**1. Select Treatment & Reason:** Choose your specialty and reason for consultation.\n**2. Choose Practitioner:** Pick your preferred doctor or therapist or view all available appointments.\n**3. Select Time Slot:** Browse the calendar and select a suitable date and time.\n**4. Enter Email:** Provide a valid email to continue and confirm booking.\n**5. Medicosearch Registration:** Enter first name, last name, and password to create an account, and accept Privacy Policy and Terms & Conditions.\n**6. Confirm Booking:** Submit email and account details to finalize your appointment.",
            DE: "**Buchungslink:** [Hier klicken zum Online-Buchen](https://functiomed.thefotoloft.ch/pages/online-termin-buchen/)\n\n**Schritt-für-Schritt-Anleitung:**\n**1. Behandlung & Grund auswählen:** Wählen Sie Ihre Fachrichtung und den Grund für die Konsultation.\n**2. Behandler wählen:** Wählen Sie Ihren bevorzugten Arzt oder Therapeuten oder zeigen Sie alle verfügbaren Termine an.\n**3. Zeitfenster auswählen:** Durchsuchen Sie den Kalender und wählen Sie ein passendes Datum und Uhrzeit.\n**4. E-Mail eingeben:** Geben Sie eine gültige E-Mail-Adresse ein, um die Buchung fortzusetzen und zu bestätigen.\n**5. Medicosearch-Registrierung:** Geben Sie Vorname, Nachname und Passwort ein, um ein Konto zu erstellen, und akzeptieren Sie Datenschutzbestimmungen und AGB.\n**6. Buchung bestätigen:** Senden Sie Ihre E-Mail und Kontodaten, um den Termin abzuschließen.",
            FR: "**Lien de réservation :** [Cliquez ici pour réserver en ligne](https://functiomed.thefotoloft.ch/pages/online-termin-buchen/)\n\n**Guide étape par étape :**\n**1. Sélectionner le traitement et le motif :** Choisissez votre spécialité et le motif de la consultation.\n**2. Choisir le praticien :** Sélectionnez votre médecin ou thérapeute préféré ou affichez tous les rendez-vous disponibles.\n**3. Choisir l'horaire :** Parcourez le calendrier et sélectionnez une date et une heure appropriées.\n**4. Saisir l'e-mail :** Fournissez une adresse e-mail valide pour continuer et confirmer la réservation.\n**5. Inscription sur Medicosearch :** Entrez votre prénom, nom et mot de passe pour créer un compte, et acceptez la politique de confidentialité et les conditions générales.\n**6. Confirmer la réservation :** Soumettez vos coordonnées e-mail et de compte pour finaliser votre rendez-vous."
        },
        category: "booking"
    }
};

// Language-specific messages
const MESSAGES = {
    EN: {
        initialGreeting: "Hi there! 👋 I'm FUNIA, your friendly assistant at Functiomed. I'm here to help you with anything you need - whether it's finding information about our services, doctors, or answering your questions. What can I help you with today?",
        placeholder: "Type your message...",
        errorMessage: "Sorry, there was an error. Please try again.",
        typingIndicator: "Typing...",
        headerTitle: "FUNIA",
        headerStatus: "● Online",
        ttsError: "Could not play audio. Please try again.",
        demoMessage: "Please click on FAQs below to get instant answers to common questions."
    },
    DE: {
        initialGreeting: "Hallo! 👋 Ich bin FUNIA, Ihre freundliche Assistentin bei Functiomed. Ich bin hier, um Ihnen bei allem zu helfen, was Sie brauchen - ob es darum geht, Informationen über unsere Dienstleistungen, Ärzte zu finden oder Ihre Fragen zu beantworten. Womit kann ich Ihnen heute helfen?",
        placeholder: "Geben Sie Ihre Nachricht ein...",
        errorMessage: "Entschuldigung, es gab einen Fehler. Bitte versuchen Sie es erneut.",
        typingIndicator: "Tippt...",
        headerTitle: "FUNIA",
        headerStatus: "● Online",
        ttsError: "Audio konnte nicht abgespielt werden. Bitte versuchen Sie es erneut.",
        demoMessage: "Bitte klicken Sie auf FAQs unten, um sofortige Antworten auf häufig gestellte Fragen zu erhalten."
    },
    FR: {
        initialGreeting: "Bonjour ! 👋 Je suis FUNIA, votre assistante amicale chez Functiomed. Je suis là pour vous aider avec tout ce dont vous avez besoin - que ce soit pour trouver des informations sur nos services, nos médecins ou répondre à vos questions. En quoi puis-je vous aider aujourd'hui ?",
        placeholder: "Tapez votre message...",
        errorMessage: "Désolé, une erreur s'est produite. Veuillez réessayer.",
        typingIndicator: "Écrit...",
        headerTitle: "FUNIA",
        headerStatus: "● En ligne",
        ttsError: "Impossible de lire l'audio. Veuillez réessayer.",
        demoMessage: "Veuillez cliquer sur FAQs ci-dessous pour obtenir des réponses instantanées aux questions fréquentes."
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
// Global voice toggle removed - using per-message speaker buttons instead
// const voiceToggle = document.getElementById('voiceToggle');
const micButton = document.getElementById('micButton');
// const pitchAnimation = document.getElementById('pitchAnimation');

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

    // Animate initial message after a short delay
    setTimeout(() => {
        const initialMessage = document.getElementById('initialMessage');
        if (initialMessage) {

            initialMessage.classList.remove('initial-hidden');
            initialMessage.classList.add('pop-in');
        }
    }, 400); // 0.4 seconds delay
}

// Setup language selector event listener
function setupLanguageSelector() {
    const languageBtns = document.querySelectorAll('.language-btn');

    // Set initial active state
    languageBtns.forEach(btn => {
        if (btn.dataset.lang === currentLanguage) {
            btn.classList.add('active');
        }

        // Add event listener
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            languageBtns.forEach(b => b.classList.remove('active'));

            // Add active class to clicked button
            btn.classList.add('active');

            // Update language
            currentLanguage = btn.dataset.lang;
            updateLanguageUI();
            loadFAQs(); // Reload FAQs in new language
        });
    });
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

// Set initial message time and add action buttons
function setInitialTime() {
    const timeElement = document.getElementById('initialTime');
    const initialMessage = timeElement ? timeElement.closest('.message.bot') : null;

    if (timeElement && initialMessage) {
        const time = getCurrentTime();
        timeElement.textContent = time;

        // Get the initial message text
        const contentDiv = initialMessage.querySelector('.message-content');
        const messageText = contentDiv ? contentDiv.textContent.trim() : '';

        // Store text in data attribute
        initialMessage.setAttribute('data-message-text', messageText);

        // Convert old structure to new footer structure - action buttons commented out
        const footerDiv = document.createElement('div');
        footerDiv.className = 'message-footer';
        footerDiv.innerHTML = `
            <div class="message-time">${time}</div>
        `;
        // COMMENTED OUT: Action buttons for initial message
        // <div class="message-actions">
        //     <button class="action-btn copy-btn" aria-label="Copy message to clipboard" title="Copy">
        //         <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        //             <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        //             <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        //         </svg>
        //         <span class="btn-text">Copy</span>
        //     </button>
        //     <button class="action-btn speaker-btn" aria-label="Listen to message" title="Listen">
        //         <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        //             <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
        //             <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
        //         </svg>
        //         <span class="btn-text">Listen</span>
        //     </button>
        // </div>

        // Remove old time element
        timeElement.remove();

        // Append new footer
        initialMessage.appendChild(footerDiv);

        // COMMENTED OUT: Event listeners for initial message action buttons
        // const copyBtn = footerDiv.querySelector('.copy-btn');
        // const speakerBtn = footerDiv.querySelector('.speaker-btn');
        //
        // if (copyBtn && speakerBtn) {
        //     copyBtn.addEventListener('click', () => copyMessageText(messageText, copyBtn));
        //     speakerBtn.addEventListener('click', () => toggleMessageAudio(initialMessage, speakerBtn));
        // }
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
    // Global voice toggle removed - using per-message speaker buttons
    // voiceToggle.addEventListener('click', toggleVoice);
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

    // Track user scroll behavior during streaming
    chatMessages.addEventListener('scroll', () => {
        const currentScroll = chatMessages.scrollTop;
        const maxScroll = chatMessages.scrollHeight - chatMessages.clientHeight;

        // Detect if user scrolled UP (not down or auto-scroll to bottom)
        if (currentScroll < lastScrollTop && currentScroll < maxScroll - 50) {
            // User scrolled up - disable auto-scroll
            userHasScrolled = true;
        } else if (currentScroll >= maxScroll - 10) {
            // User is at bottom - re-enable auto-scroll
            userHasScrolled = false;
        }

        // Update last position
        lastScrollTop = currentScroll;
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

// Helper function to find matching FAQ based on exact question match
function findMatchingFAQ(userQuery) {
    if (!userQuery) return null;

    // Normalize user query for comparison (trim, lowercase, remove punctuation)
    const normalizedQuery = userQuery.trim().toLowerCase().replace(/[?!.,;:]/g, '');

    // Search through all FAQs
    for (const faqId in faqCache) {
        const faq = faqCache[faqId];

        // Check if question matches in current language
        if (faq.question && faq.question[currentLanguage]) {
            // Normalize FAQ question (lowercase, remove punctuation)
            const faqQuestion = faq.question[currentLanguage].toLowerCase().replace(/[?!.,;:]/g, '');

            // Exact match (case-insensitive, punctuation-insensitive)
            if (normalizedQuery === faqQuestion) {
                return faq;
            }
        }
    }

    return null;
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

    // Simulate a short delay for better UX
    await new Promise(resolve => setTimeout(resolve, 800));

    hideTypingIndicator();

    // Check if user query matches any FAQ question exactly
    const matchedFAQ = findMatchingFAQ(message);

    if (matchedFAQ) {
        // Return FAQ answer immediately
        const answer = matchedFAQ.answer[currentLanguage];
        addMessage(answer, 'bot');
    } else {
        // Return demo message in the selected language
        const messages = MESSAGES[currentLanguage];
        addMessage(messages.demoMessage, 'bot');
    }
}

// Streaming message with stop capability
async function sendMessageStreaming(message) {
    // Show typing indicator while preparing response
    showTypingIndicator();

    // Simulate a short delay for better UX
    await new Promise(resolve => setTimeout(resolve, 800));

    hideTypingIndicator();

    // Check if user query matches any FAQ question exactly
    const matchedFAQ = findMatchingFAQ(message);

    if (matchedFAQ) {
        // Return FAQ answer immediately
        const answer = matchedFAQ.answer[currentLanguage];
        addMessage(answer, 'bot');
    } else {
        // Return demo message in the selected language
        const messages = MESSAGES[currentLanguage];
        addMessage(messages.demoMessage, 'bot');
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
                            // Reset user scroll flag for new message (allow auto-scroll for new response)
                            userHasScrolled = false;
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
function addMessage(text, sender, sources = null, confidence = null, autoScroll = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const time = getCurrentTime();

    // Convert markdown to HTML for bot messages
    const formattedText = sender === 'bot' ? markdownToHtml(text) : escapeHtml(text);

    // Store original text in data attribute for copy/TTS functionality
    messageDiv.setAttribute('data-message-text', text);

    if (sender === 'bot') {
        // Bot messages - action buttons commented out
        messageDiv.innerHTML = `
            <div class="message-content">${formattedText}</div>
            <div class="message-footer">
                <div class="message-time">${time}</div>
            </div>
        `;
        // COMMENTED OUT: Action buttons (Copy & Listen)
        // <div class="message-actions">
        //     <button class="action-btn copy-btn" aria-label="Copy message to clipboard" title="Copy">
        //         <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        //             <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        //             <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        //         </svg>
        //         <span class="btn-text">Copy</span>
        //     </button>
        //     <button class="action-btn speaker-btn" aria-label="Listen to message" title="Listen">
        //         <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        //             <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
        //             <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
        //         </svg>
        //         <span class="btn-text">Listen</span>
        //     </button>
        // </div>
    } else {
        // User messages without action buttons
        messageDiv.innerHTML = `
            <div class="message-content">${formattedText}</div>
            <div class="message-time">${time}</div>
        `;
    }

    chatMessages.appendChild(messageDiv);

    // COMMENTED OUT: Event listeners for action buttons
    // if (sender === 'bot') {
    //     const copyBtn = messageDiv.querySelector('.copy-btn');
    //     const speakerBtn = messageDiv.querySelector('.speaker-btn');
    //
    //     copyBtn.addEventListener('click', () => copyMessageText(text, copyBtn));
    //     speakerBtn.addEventListener('click', () => toggleMessageAudio(messageDiv, speakerBtn));
    // }

    // Only auto-scroll if requested (default: true)
    if (autoScroll) {
        scrollToBottom();
    }

    // Store in conversation history
    conversationHistory.push({
        text: text,
        sender: sender,
        timestamp: new Date().toISOString()
    });

    // Return the message element for potential scrolling to specific position
    return messageDiv;
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

// Scroll to bottom of messages (throttled for smooth streaming)
function scrollToBottom() {
    if (scrollPending) return;

    scrollPending = true;
    requestAnimationFrame(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
        lastScrollTop = chatMessages.scrollTop;
        scrollPending = false;
    });
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

        // Only auto-scroll if user hasn't manually scrolled up
        if (!userHasScrolled) {
            scrollToBottom();
        }
    }
}

// Finalize streaming message (remove streaming class)
function finalizeStreamingMessage(messageDiv, text, wasCancelled = false, hasError = false) {
    messageDiv.classList.remove('streaming');

    // Store original text in data attribute for copy/TTS functionality
    messageDiv.setAttribute('data-message-text', text);

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

    // Add message footer - action buttons commented out
    if (!messageDiv.querySelector('.message-footer') && !hasError) {
        const timeDiv = messageDiv.querySelector('.message-time');
        const time = timeDiv ? timeDiv.textContent : getCurrentTime();

        // Create footer with time only
        const footerDiv = document.createElement('div');
        footerDiv.className = 'message-footer';
        footerDiv.innerHTML = `
            <div class="message-time">${time}</div>
        `;
        // COMMENTED OUT: Action buttons for streaming messages
        // <div class="message-actions">
        //     <button class="action-btn copy-btn" aria-label="Copy message to clipboard" title="Copy">
        //         <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        //             <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        //             <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        //         </svg>
        //         <span class="btn-text">Copy</span>
        //     </button>
        //     <button class="action-btn speaker-btn" aria-label="Listen to message" title="Listen">
        //         <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        //             <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
        //             <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
        //         </svg>
        //         <span class="btn-text">Listen</span>
        //     </button>
        // </div>

        // Remove old time div if exists
        if (timeDiv) {
            timeDiv.remove();
        }

        // Append footer
        messageDiv.appendChild(footerDiv);

        // COMMENTED OUT: Event listeners for streaming message action buttons
        // const copyBtn = footerDiv.querySelector('.copy-btn');
        // const speakerBtn = footerDiv.querySelector('.speaker-btn');
        //
        // copyBtn.addEventListener('click', () => copyMessageText(text, copyBtn));
        // speakerBtn.addEventListener('click', () => toggleMessageAudio(messageDiv, speakerBtn));
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

// Handle FAQ button click - response with typing indicator delay
async function handleFAQClick(faqId) {
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

    // Display question as user message (with auto-scroll to show the question)
    const questionElement = addMessage(question, 'user', null, null, true);

    // Show typing indicator
    showTypingIndicator();

    // Wait 1500ms to simulate natural typing delay
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Hide typing indicator
    hideTypingIndicator();

    // Reset user scroll flag for new message (allow auto-scroll for new response)
    userHasScrolled = false;

    // Create streaming message container
    const messageDiv = createStreamingMessage();

    // Stream the answer word by word
    // Split by spaces but preserve newlines and markdown formatting
    const words = answer.split(/(\s+)/); // Keep whitespace including newlines
    let fullText = '';

    for (let i = 0; i < words.length; i++) {
        fullText += words[i];

        // Update the message with accumulated text
        updateStreamingMessage(messageDiv, fullText);

        // Delay between words for smooth streaming (50ms for nice consistent speed)
        // Skip delay for whitespace-only tokens
        if (words[i].trim().length > 0) {
            await new Promise(resolve => setTimeout(resolve, 50));
        }
    }

    // Finalize the streaming message
    finalizeStreamingMessage(messageDiv, fullText);

    // Scroll to show the question at the top of the chat
    if (questionElement) {
        questionElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    // Don't hide FAQs - keep them visible like inspiration widget
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

// Toggle voice output - DEPRECATED: Global voice toggle removed
// Now using per-message speaker buttons instead
async function toggleVoice() {
    console.log('Global voice toggle deprecated - use per-message speaker buttons');
    // Kept for backward compatibility, does nothing
}

// Show speaking animation - DEPRECATED: Global voice toggle removed
function showSpeakingAnimation() {
    // Global animation removed - using per-message button states instead
}

// Hide speaking animation - DEPRECATED: Global voice toggle removed
function hideSpeakingAnimation() {
    // Global animation removed - using per-message button states instead
}

// ============================================================================
// Per-Message Action Functions (Copy & TTS)
// ============================================================================

// Track currently playing message
let currentPlayingMessage = null;
let currentPlayingButton = null;

// Copy message text to clipboard
async function copyMessageText(text, buttonElement) {
    try {
        // Try modern Clipboard API first
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
            showCopySuccess(buttonElement);
        } else {
            // Fallback for older browsers
            fallbackCopyText(text);
            showCopySuccess(buttonElement);
        }
    } catch (error) {
        console.error('Copy failed:', error);
        showCopyError(buttonElement);
    }
}

// Fallback copy method for older browsers
function fallbackCopyText(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        textArea.remove();
    } catch (error) {
        console.error('Fallback copy failed:', error);
        textArea.remove();
        throw error;
    }
}

// Show copy success feedback
function showCopySuccess(buttonElement) {
    const originalHTML = buttonElement.innerHTML;

    // Change to checkmark
    buttonElement.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <span class="btn-text">Copied!</span>
    `;
    buttonElement.classList.add('copy-success');

    // Revert after 1.5 seconds
    setTimeout(() => {
        buttonElement.innerHTML = originalHTML;
        buttonElement.classList.remove('copy-success');
    }, 1500);
}

// Show copy error feedback
function showCopyError(buttonElement) {
    const originalHTML = buttonElement.innerHTML;

    buttonElement.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
        <span class="btn-text">Failed</span>
    `;
    buttonElement.classList.add('copy-error');

    setTimeout(() => {
        buttonElement.innerHTML = originalHTML;
        buttonElement.classList.remove('copy-error');
    }, 1500);
}

// Toggle audio playback for a specific message
async function toggleMessageAudio(messageDiv, buttonElement) {
    console.log('toggleMessageAudio called');
    const text = messageDiv.getAttribute('data-message-text');

    if (!text) {
        console.error('No message text found in data-message-text attribute');
        console.log('MessageDiv:', messageDiv);
        return;
    }

    console.log('Message text found:', text.substring(0, 50) + '...');

    // If this message is currently playing, stop it
    if (currentPlayingMessage === messageDiv && currentAudio && !currentAudio.paused) {
        console.log('Stopping currently playing message');
        stopMessageAudio(buttonElement);
        return;
    }

    // Stop any other playing audio
    if (currentPlayingMessage && currentPlayingButton) {
        console.log('Stopping other playing message');
        stopMessageAudio(currentPlayingButton);
    }

    // Start playing this message
    console.log('Starting audio playback');
    await playMessageAudio(text, messageDiv, buttonElement);
}

// Play audio for a specific message
async function playMessageAudio(text, messageDiv, buttonElement) {
    try {
        // Update button to loading state
        updateSpeakerButtonState(buttonElement, 'loading');

        // Store reference
        currentPlayingMessage = messageDiv;
        currentPlayingButton = buttonElement;

        // Clean up previous audio
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }
        cleanupAudioBlob();

        // Strip markdown formatting for clean audio
        const cleanText = stripMarkdownForTTS(text);

        console.log(`Generating TTS for message: "${cleanText.substring(0, 50)}..." (${currentLanguage})`);

        // Call TTS API
        const response = await fetch(`${API_BASE_URL}/api/v1/tts/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: cleanText,
                language: currentLanguage
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
            updateSpeakerButtonState(buttonElement, 'playing');
        });

        currentAudio.addEventListener('ended', () => {
            console.log('Audio playback finished');
            updateSpeakerButtonState(buttonElement, 'idle');
            cleanupAudioBlob();
            currentPlayingMessage = null;
            currentPlayingButton = null;
        });

        currentAudio.addEventListener('error', (e) => {
            console.error('Audio playback error:', e);
            updateSpeakerButtonState(buttonElement, 'error');
            cleanupAudioBlob();
            currentPlayingMessage = null;
            currentPlayingButton = null;
        });

        // Start playback
        await currentAudio.play();

    } catch (error) {
        console.error('TTS error:', error);
        updateSpeakerButtonState(buttonElement, 'error');
        currentPlayingMessage = null;
        currentPlayingButton = null;
    }
}

// Stop audio playback for a message
function stopMessageAudio(buttonElement) {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio = null;
    }
    cleanupAudioBlob();
    updateSpeakerButtonState(buttonElement, 'idle');
    currentPlayingMessage = null;
    currentPlayingButton = null;
}

// Update speaker button visual state
function updateSpeakerButtonState(buttonElement, state) {
    // Remove all state classes
    buttonElement.classList.remove('loading', 'playing', 'error');

    const originalSVG = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
        </svg>
    `;

    switch (state) {
        case 'loading':
            buttonElement.classList.add('loading');
            buttonElement.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="32">
                        <animate attributeName="stroke-dashoffset" from="32" to="0" dur="1s" repeatCount="indefinite"/>
                    </circle>
                </svg>
                <span class="btn-text">Loading...</span>
            `;
            break;

        case 'playing':
            buttonElement.classList.add('playing');
            buttonElement.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="6" y="4" width="4" height="16"></rect>
                    <rect x="14" y="4" width="4" height="16"></rect>
                </svg>
                <span class="btn-text">Stop</span>
            `;
            break;

        case 'error':
            buttonElement.classList.add('error');
            buttonElement.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <span class="btn-text">Error</span>
            `;
            setTimeout(() => {
                buttonElement.classList.remove('error');
                buttonElement.innerHTML = originalSVG + '<span class="btn-text">Listen</span>';
            }, 2000);
            break;

        case 'idle':
        default:
            buttonElement.innerHTML = originalSVG + '<span class="btn-text">Listen</span>';
            break;
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
