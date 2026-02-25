/**
 * FIPE Hunter — Landing Page
 * Style: Finpay-inspired light/white, split hero, teal accent, professional B2B
 * Template base: minimal-light + custom split-hero
 * Stack: React 18 + Tailwind CSS + React Router v6
 */

import { Link } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

// ─── Animation variants ────────────────────────────────────────────────────────

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};

// ─── Types ─────────────────────────────────────────────────────────────────────

interface Feature {
  icon: string;
  title: string;
  description: string;
}

interface Step {
  n: string;
  title: string;
  desc: string;
}

interface Stat {
  target: number;
  prefix?: string;
  suffix?: string;
  label: string;
}

// ─── DATA ──────────────────────────────────────────────────────────────────────

const PRODUCT_NAME = "FIPE Hunter";
const TAGLINE = "Tabela FIPE oficial · Score 0–100";

// Hero
const HERO_HEADLINE_MAIN = "Encontre carros abaixo do preço";
const HERO_HEADLINE_ACCENT = "antes que sumam.";
const HERO_SUBHEADLINE =
  "O FIPE Hunter rastreia portais de venda, compara cada anúncio com a tabela FIPE e entrega um ranking de oportunidades reais — em segundos.";
const CTA_LABEL = "Ver oportunidades";
const CTA_SUBTITLE = "Demo pública · sem cadastro.";
const SECONDARY_CTA_LABEL = "Como funciona";
const CTA_TO = "/app/opportunities";

// Features
const FEATURES_HEADING = "Busca inteligente que trabalha por você";
const FEATURES_SUBHEADING =
  "Pipeline de três estágios — do scraper ao score — sem intervenção manual.";
const FEATURES: Feature[] = [
  {
    icon: "🔍",
    title: "Scraper sob demanda",
    description:
      "Informe marca, modelo e ano. O sistema coleta anúncios frescos dos principais portais em tempo real.",
  },
  {
    icon: "📊",
    title: "Comparação com a FIPE",
    description:
      "Cada anúncio é comparado automaticamente com o preço de referência oficial da tabela FIPE.",
  },
  {
    icon: "🏆",
    title: "Ranking de oportunidades",
    description:
      "Os resultados são rankeados por score de desconto. As melhores ofertas sempre no topo.",
  },
];

// Stats
const STATS: Stat[] = [
  { target: 30,  prefix: "< ", suffix: "s", label: "Tempo médio de busca" },
  { target: 100, prefix: "0–",              label: "Score de desconto por veículo" },
  { target: 1,   suffix: "+",               label: "Portal monitorado em produção" },
];

// Steps
const STEPS: Step[] = [
  {
    n: "1",
    title: "Selecione marca e modelo",
    desc: "Use o buscador para informar o veículo que você procura.",
  },
  {
    n: "2",
    title: "Sistema busca e compara",
    desc: "O scraper coleta anúncios e compara cada um com a tabela FIPE oficial.",
  },
  {
    n: "3",
    title: "Analise e aja",
    desc: "Veja o ranking de oportunidades, salve favoritos e acesse o anúncio original.",
  },
];

// Bottom CTA
const BOTTOM_CTA_HEADING = "Pronto para encontrar seu próximo carro?";
const BOTTOM_CTA_COPY = "Demo em produção, sem instalação, sem cadastro.";

// Footer
const FOOTER_NOTE = "Demo · fipe-hunter-api.onrender.com";

// ─── Navbar ────────────────────────────────────────────────────────────────────

function Navbar() {
  return (
    <nav
      className="sticky top-0 z-50 flex items-center justify-between px-6 md:px-10 py-4 bg-white/95 backdrop-blur-sm border-b border-gray-100"
      aria-label="Navegação principal"
    >
      <span className="flex items-center gap-2 font-bold text-gray-900 text-lg tracking-tight">
        <span aria-hidden="true">🏎️</span>
        {PRODUCT_NAME}
      </span>
      <div className="flex items-center gap-4">
        <a
          href="#como-funciona"
          className="hidden sm:block text-sm text-gray-500 hover:text-gray-900 transition-colors"
        >
          {SECONDARY_CTA_LABEL}
        </a>
        <Link
          to={CTA_TO}
          className="px-5 py-2 bg-teal-500 hover:bg-teal-600 text-white text-sm font-semibold rounded-xl transition-colors"
        >
          {CTA_LABEL}
        </Link>
      </div>
    </nav>
  );
}

// ─── OpportunityMockup (hero right side) ──────────────────────────────────────

function OpportunityMockup() {
  return (
    <div className="relative w-full max-w-sm mx-auto lg:mx-0">
      {/* Floating badge */}
      <div className="absolute -top-3 -right-3 z-10 bg-teal-500 text-white text-xs font-bold px-3 py-1.5 rounded-2xl shadow-lg">
        🔥 Oportunidade
      </div>

      {/* Main card */}
      <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 p-7 space-y-5">
        {/* Header row */}
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-gray-400 bg-gray-50 px-3 py-1 rounded-lg border border-gray-100">
            São Paulo
          </span>
          <div className="flex items-center gap-1.5 bg-teal-50 text-teal-700 text-xs font-bold px-3 py-1 rounded-lg">
            <span>Score</span>
            <span className="text-base font-extrabold">84</span>
          </div>
        </div>

        {/* Vehicle + price */}
        <div>
          <p className="text-sm text-gray-400 font-medium">Honda Civic EXL 2019</p>
          <p className="text-4xl font-extrabold text-gray-900 mt-1 tracking-tight">
            R$ 68.500
          </p>
          <p className="text-sm text-gray-400 mt-1">
            Tabela FIPE:{" "}
            <span className="line-through text-gray-400">R$ 84.200</span>
          </p>
        </div>

        {/* Discount + savings */}
        <div className="flex gap-3">
          <div className="flex-1 bg-teal-50 rounded-2xl p-4 text-center">
            <p className="text-2xl font-extrabold text-teal-600 leading-none">
              -19%
            </p>
            <p className="text-xs text-gray-400 mt-1">abaixo da FIPE</p>
          </div>
          <div className="flex-1 bg-gray-50 rounded-2xl p-4 text-center">
            <p className="text-lg font-extrabold text-gray-700 leading-none">
              R$ 15.700
            </p>
            <p className="text-xs text-gray-400 mt-1">economia</p>
          </div>
        </div>

        {/* CTA button */}
        <button
          className="w-full bg-teal-500 hover:bg-teal-600 text-white rounded-2xl py-3.5 text-sm font-semibold transition-colors"
          type="button"
        >
          Ver anúncio →
        </button>
      </div>

      {/* Decorative background blob */}
      <div
        className="absolute -z-10 inset-0 translate-x-4 translate-y-4 rounded-3xl bg-teal-100 opacity-50"
        aria-hidden="true"
      />
    </div>
  );
}

// ─── Hero ──────────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section
      className="min-h-[90vh] flex items-center px-6 md:px-10 bg-white"
      aria-label="Hero"
    >
      <div className="max-w-6xl mx-auto w-full grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center py-20">
        {/* Left — copy */}
        <motion.div
          className="space-y-8"
          initial="hidden"
          animate="show"
          variants={stagger}
        >
          <motion.span
            variants={fadeUp}
            className="inline-block text-xs font-mono tracking-widest text-teal-500 uppercase"
          >
            {TAGLINE}
          </motion.span>
          <motion.h1
            variants={fadeUp}
            className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-gray-900 leading-tight"
          >
            {HERO_HEADLINE_MAIN}{" "}
            <span className="text-teal-500">{HERO_HEADLINE_ACCENT}</span>
          </motion.h1>
          <motion.p variants={fadeUp} className="text-lg text-gray-500 leading-relaxed max-w-lg">
            {HERO_SUBHEADLINE}
          </motion.p>
          <motion.div variants={fadeUp} className="flex flex-col sm:flex-row gap-4">
            <Link
              to={CTA_TO}
              className="px-8 py-4 bg-teal-500 hover:bg-teal-600 text-white font-semibold rounded-2xl transition-colors text-center shadow-sm shadow-teal-200"
            >
              {CTA_LABEL} →
            </Link>
            <a
              href="#como-funciona"
              className="px-8 py-4 border border-gray-200 hover:border-gray-400 text-gray-600 rounded-2xl transition-colors text-center"
            >
              {SECONDARY_CTA_LABEL}
            </a>
          </motion.div>
          <motion.p variants={fadeUp} className="text-sm text-gray-400">{CTA_SUBTITLE}</motion.p>
        </motion.div>

        {/* Right — mockup card */}
        <motion.div
          className="flex justify-center lg:justify-end"
          initial={{ opacity: 0, x: 40, scale: 0.95 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.3 }}
        >
          <OpportunityMockup />
        </motion.div>
      </div>
    </section>
  );
}

// ─── Features ─────────────────────────────────────────────────────────────────

function Features() {
  return (
    <section
      id="como-funciona"
      className="py-24 px-6 md:px-10 bg-gray-50 scroll-mt-16"
      aria-label={FEATURES_HEADING}
    >
      <div className="max-w-6xl mx-auto space-y-16">
        <div className="text-center space-y-4 max-w-2xl mx-auto">
          <span className="text-xs font-mono tracking-widest text-teal-500 uppercase">
            Como funciona
          </span>
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
            {FEATURES_HEADING}
          </h2>
          <p className="text-gray-500 leading-relaxed">{FEATURES_SUBHEADING}</p>
        </div>

        <motion.ul
          className="grid grid-cols-1 md:grid-cols-3 gap-8 list-none p-0"
          variants={stagger}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
        >
          {FEATURES.map((f) => (
            <motion.li
              key={f.title}
              variants={fadeUp}
              className="bg-white rounded-3xl p-8 border border-gray-100 shadow-sm space-y-4 hover:shadow-md hover:border-teal-100 transition-all"
            >
              <span className="text-4xl" role="img" aria-hidden="true">
                {f.icon}
              </span>
              <h3 className="text-base font-semibold text-gray-900">
                {f.title}
              </h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                {f.description}
              </p>
            </motion.li>
          ))}
        </motion.ul>
      </div>
    </section>
  );
}

// ─── useCountUp ────────────────────────────────────────────────────────────────

function useCountUp(target: number, duration = 1500) {
  const [count, setCount] = useState(0);
  const [triggered, setTriggered] = useState(false);
  const ref = useRef<HTMLLIElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setTriggered(true); observer.disconnect(); } },
      { threshold: 0.5 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!triggered) return;
    let start: number | null = null;
    const step = (timestamp: number) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      setCount(Math.floor(progress * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [triggered, target, duration]);

  return { count, ref };
}

// ─── Stats ─────────────────────────────────────────────────────────────────────

function StatCard({ stat }: { stat: Stat }) {
  const { count, ref } = useCountUp(stat.target);
  return (
    <li ref={ref} className="rounded-3xl border border-gray-100 p-8 text-center space-y-2 hover:border-teal-200 hover:shadow-sm transition-all">
      <p className="text-4xl font-extrabold text-teal-500">
        {stat.prefix}{count}{stat.suffix}
      </p>
      <p className="text-gray-500 text-sm">{stat.label}</p>
    </li>
  );
}

function Stats() {
  return (
    <section className="py-20 px-6 md:px-10 bg-white" aria-label="Números">
      <div className="max-w-6xl mx-auto space-y-12">
        <div className="text-center space-y-2">
          <span className="text-xs font-mono tracking-widest text-teal-500 uppercase">
            Por que usar
          </span>
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
            FIPE Hunter em números
          </h2>
        </div>

        <ul className="grid grid-cols-1 md:grid-cols-3 gap-8 list-none p-0">
          {STATS.map((s) => <StatCard key={s.label} stat={s} />)}
        </ul>
      </div>
    </section>
  );
}

// ─── Steps ─────────────────────────────────────────────────────────────────────

function Steps() {
  return (
    <section
      className="py-24 px-6 md:px-10 bg-gray-900 text-white"
      aria-label="Como usar"
    >
      <div className="max-w-6xl mx-auto space-y-16">
        <div className="space-y-4">
          <span className="text-xs font-mono tracking-widest text-teal-400 uppercase">
            Como usar
          </span>
          <h2 className="text-3xl md:text-4xl font-bold max-w-lg leading-tight">
            Três passos para encontrar sua oportunidade.
          </h2>
        </div>

        <motion.ol
          className="grid grid-cols-1 md:grid-cols-3 gap-10 list-none p-0"
          variants={stagger}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
        >
          {STEPS.map((s) => (
            <motion.li key={s.n} variants={fadeUp} className="space-y-4">
              <span className="text-6xl font-extrabold text-teal-500 opacity-80 leading-none block">
                {s.n}
              </span>
              <h3 className="text-lg font-semibold text-white">{s.title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{s.desc}</p>
            </motion.li>
          ))}
        </motion.ol>
      </div>
    </section>
  );
}

// ─── CallToAction ──────────────────────────────────────────────────────────────

function CallToAction() {
  return (
    <section
      className="py-24 px-6 md:px-10 bg-teal-600 text-white"
      aria-label="Chamada para ação"
    >
      <motion.div
        className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-10"
        variants={fadeUp}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true }}
      >
        <div className="space-y-3 max-w-xl">
          <span className="text-xs font-mono tracking-widest text-teal-200 uppercase">
            Comece agora
          </span>
          <h2 className="text-3xl md:text-4xl font-bold leading-tight">
            {BOTTOM_CTA_HEADING}
          </h2>
          <p className="text-teal-100 text-sm leading-relaxed">
            {BOTTOM_CTA_COPY}
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-4 shrink-0">
          <Link
            to={CTA_TO}
            className="px-8 py-4 bg-white text-teal-700 font-bold rounded-2xl hover:bg-teal-50 transition-colors text-center shadow-md"
          >
            {CTA_LABEL} →
          </Link>
          <a
            href="#como-funciona"
            className="px-8 py-4 border border-teal-400 text-white rounded-2xl hover:border-white hover:bg-teal-700 transition-colors text-center"
          >
            {SECONDARY_CTA_LABEL}
          </a>
        </div>
      </motion.div>
    </section>
  );
}

// ─── Footer ────────────────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer className="py-10 px-6 md:px-10 bg-white border-t border-gray-100">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <span className="flex items-center gap-2 font-semibold text-gray-700">
          <span aria-hidden="true">🏎️</span>
          {PRODUCT_NAME}
        </span>
        <p className="text-sm text-gray-400">{FOOTER_NOTE}</p>
      </div>
    </footer>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────────

export default function LandingPage() {
  return (
    <div className="font-sans antialiased bg-white text-gray-900">
      <Navbar />
      <Hero />
      <Features />
      <Stats />
      <Steps />
      <CallToAction />
      <Footer />
    </div>
  );
}
