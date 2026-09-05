export const SITE = {
  name: "Cima Pilates",
  legal: "Cima Pilates SpA",
  location: "Av. Concha y Toro 3346, Local 41, Puente Alto",
  metro: "Metro Sótero del Río",
  hoursWeek: "Lunes a viernes · 07:10 – 12:00 y 16:00 – 21:00 hrs",
  hoursSaturday: "Sábado · 09:00 – 14:00 hrs",
  singleClass: "$9.990",
}

export type Plan = {
  icon: string
  credits: string
  frequency: string
  monthly: string
  quarterly: string
  semester: string
}

export const PLANS: Plan[] = [
  {
    icon: "04",
    credits: "4 clases al mes",
    frequency: "1 vez por semana",
    monthly: "$35.990",
    quarterly: "$96.990",
    semester: "$188.990",
  },
  {
    icon: "08",
    credits: "8 clases al mes",
    frequency: "2 veces por semana",
    monthly: "$56.990",
    quarterly: "$153.990",
    semester: "$298.990",
  },
  {
    icon: "12",
    credits: "12 clases al mes",
    frequency: "3 veces por semana",
    monthly: "$79.990",
    quarterly: "$215.990",
    semester: "$419.990",
  },
  {
    icon: "16",
    credits: "16 clases al mes",
    frequency: "4 veces por semana",
    monthly: "$85.990",
    quarterly: "$232.990",
    semester: "$450.990",
  },
]

export const METHOD_STEPS = [
  {
    step: "01",
    title: "Evaluación inicial",
    text: "Antes de tu primera clase realizamos una anamnesis y conocemos tu historia de movimiento, lesiones previas y objetivos. Así adaptamos el reformer a tu cuerpo, y no al revés.",
  },
  {
    step: "02",
    title: "Trabajo en reformer",
    text: "Contamos con 8 camas reformer distribuidas en dos bloques horarios. El sistema de poleas, resortes y carro deslizante crea resistencia progresiva y asistida que protege tus articulaciones mientras activa la musculatura profunda.",
  },
  {
    step: "03",
    title: "Progresión guiada",
    text: "Cada sesión se construye sobre los principios clásicos del método: concentración, control, centro, fluidez, precisión y respiración. Avanzas a tu ritmo, con acompañamiento real en grupos reducidos.",
  },
]

export const BENEFITS = [
  {
    title: "Core fuerte y estable",
    text: "El método trabaja desde el centro —abdomen, suelo pélvico y espalda baja— construyendo una base de fuerza que sostiene cada movimiento de tu día.",
  },
  {
    title: "Postura y alineación",
    text: "Reeduca la forma en que te paras, te sientas y te mueves, aliviando tensiones de cuello, hombros y zona lumbar generadas por el trabajo y la rutina.",
  },
  {
    title: "Movilidad sin impacto",
    text: "El reformer permite ganar rango articular y flexibilidad de manera segura, ideal para todas las edades y etapas, incluido el postparto.",
  },
  {
    title: "Cuerpo tonificado",
    text: "El trabajo de resistencia con resortes esculpe y alarga la musculatura sin sobrecargar, definiendo brazos, piernas y abdomen.",
  },
  {
    title: "Mente en calma",
    text: "La respiración consciente y la concentración del método reducen el estrés y te devuelven la conexión con tu cuerpo.",
  },
  {
    title: "Bienestar sostenido",
    text: "La práctica regular mejora el sueño, la energía y la confianza. Más que ejercicio, es un hábito que cuida de ti.",
  },
]

export const GALLERY = [
  {
    src: "/img/studio-room.png",
    title: "La sala reformer",
    text: "Ocho camas reformer, luz natural y un espacio limpio pensado para concentrarte solo en ti.",
  },
  {
    src: "/img/detail-reformer.png",
    title: "Equipamiento profesional",
    text: "Resortes calibrados, poleas y carro deslizante para un trabajo preciso, seguro y progresivo.",
  },
  {
    src: "/img/wellness-women.png",
    title: "Comunidad de mujeres",
    text: "Grupos reducidos en un ambiente cercano, donde entrenar se siente como un encuentro.",
  },
]
