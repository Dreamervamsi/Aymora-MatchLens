import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Compass, Layers, HeartHandshake, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

/**
 * Polished MatchLens Welcome Experience Page.
 * Communicates reciprocal compatibility and provides CTA to start onboarding.
 */
export const WelcomePage = () => {
  const navigate = useNavigate();

  const handleStartOnboarding = () => {
    navigate('/interview');
  };

  const steps = [
    {
      num: '01',
      title: 'Tell us about yourself',
      description: 'Engage in a natural, conversational AI onboarding interview to articulate your core values, lifestyle preferences, and relationship priorities.',
      icon: Compass,
      badge: 'Conversational AI',
    },
    {
      num: '02',
      title: 'Explore relationship scenarios',
      description: 'Evaluate practical real-world scenarios covering conflict resolution, decision-making, and growth to clarify your actions and partner expectations.',
      icon: Layers,
      badge: 'Scenario Assessment',
    },
    {
      num: '03',
      title: 'Discover compatible matches',
      description: 'Receive multi-dimensional, transparent reciprocal compatibility recommendations ranked by actual alignment across all dimensions.',
      icon: HeartHandshake,
      badge: 'Reciprocal Engine',
    },
  ];

  const highlights = [
    'No endless superficial swiping',
    'Bidirectional reciprocal compatibility',
    'Transparent match explanations',
  ];

  // Subtle entrance animation setup
  const fadeUpVariant = {
    hidden: { opacity: 0, y: 12 },
    visible: (i = 0) => ({
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.4,
        ease: [0.25, 0.1, 0.25, 1],
        delay: i * 0.1,
      },
    }),
  };

  return (
    <div className="flex-1 flex flex-col justify-center max-w-5xl mx-auto w-full py-4 md:py-8">
      {/* Hero Section */}
      <motion.div
        initial="hidden"
        animate="visible"
        variants={fadeUpVariant}
        custom={0}
        className="text-center max-w-3xl mx-auto mb-12 sm:mb-16"
      >
        <div className="inline-flex items-center gap-2 mb-4">
          <Badge variant="rose" size="lg" icon={Sparkles}>
            AI-Assisted Matchmaking
          </Badge>
        </div>

        <h1 className="text-3xl sm:text-5xl font-bold text-[#2B2D42] tracking-tight leading-[1.15] mb-6">
          Find meaningful compatibility beyond surface profiles.
        </h1>

        <p className="text-base sm:text-lg text-[#5C627A] leading-relaxed mb-8 max-w-2xl mx-auto font-normal">
          MatchLens combines conversational AI onboarding with real-world relationship scenario assessments to discover deep, bidirectional reciprocal matches.
        </p>

        {/* Primary Call to Action */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-6">
          <Button
            size="lg"
            variant="primary"
            icon={ArrowRight}
            onClick={handleStartOnboarding}
            className="w-full sm:w-auto text-base px-8 py-4 shadow-md hover:shadow-lg"
          >
            Find My Matches
          </Button>
        </div>

        {/* Value Bullet Highlights */}
        <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs font-medium text-[#5C627A]">
          {highlights.map((item, idx) => (
            <div key={idx} className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#E07A5F]" />
              <span>{item}</span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* 3-Step Process Explanation */}
      <motion.div
        initial="hidden"
        animate="visible"
        variants={fadeUpVariant}
        custom={1}
        className="mb-12"
      >
        <div className="text-center mb-8">
          <h2 className="text-xl font-bold text-[#2B2D42] tracking-tight">
            How MatchLens Works
          </h2>
          <p className="text-xs text-[#5C627A] mt-1">
            A simple 3-step process designed for genuine relationship readiness
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {steps.map((step, idx) => {
            const IconComponent = step.icon;
            return (
              <motion.div
                key={step.num}
                initial="hidden"
                animate="visible"
                variants={fadeUpVariant}
                custom={idx + 2}
              >
                <Card
                  hover
                  className="h-full flex flex-col justify-between relative overflow-hidden group"
                >
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-10 h-10 rounded-xl bg-[#FDF0ED] text-[#E07A5F] border border-[#F2C0B6] flex items-center justify-center font-bold text-sm">
                        <IconComponent className="w-5 h-5" />
                      </div>
                      <span className="text-xs font-bold text-[#A0A4B8] tracking-widest font-mono">
                        {step.num}
                      </span>
                    </div>

                    <h3 className="text-base font-semibold text-[#2B2D42] mb-2 tracking-tight group-hover:text-[#E07A5F] transition-colors">
                      {step.title}
                    </h3>

                    <p className="text-xs text-[#5C627A] leading-relaxed mb-6">
                      {step.description}
                    </p>
                  </div>

                  <div>
                    <Badge variant="stone" size="sm">
                      {step.badge}
                    </Badge>
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* Trust & Privacy Notice Card */}
      <motion.div
        initial="hidden"
        animate="visible"
        variants={fadeUpVariant}
        custom={5}
      >
        <Card className="bg-[#FAF6F0]/60 border-[#E8E3DC] p-6 text-center max-w-2xl mx-auto">
          <div className="flex items-center justify-center gap-2 text-xs font-semibold text-[#2B2D42] mb-1">
            <ShieldCheck className="w-4 h-4 text-[#E07A5F]" />
            <span>Thoughtful & Private</span>
          </div>
          <p className="text-xs text-[#5C627A] leading-relaxed">
            Your conversational responses and scenario selections are strictly evaluated for mutual compatibility. No raw personal chat transcripts are shared with potential matches.
          </p>
        </Card>
      </motion.div>
    </div>
  );
};

export default WelcomePage;
