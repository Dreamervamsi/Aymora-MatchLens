import React from 'react';
import { HeartHandshake, Clock, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card, Button, Badge } from '../components/ui';

/**
 * Placeholder component for upcoming Match Discovery route (/matches).
 */
export const MatchesPlaceholder = () => {
  return (
    <div className="max-w-2xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-12">
      <Card className="text-center p-8 md:p-12 w-full">
        <div className="w-16 h-16 rounded-2xl bg-[#FDF0ED] border border-[#F2C0B6] text-[#E07A5F] flex items-center justify-center mx-auto mb-6">
          <HeartHandshake className="w-8 h-8" />
        </div>

        <Badge variant="stone" className="mb-4">
          Upcoming Feature — Phase 7.5
        </Badge>

        <h1 className="text-2xl font-bold text-[#2B2D42] tracking-tight mb-3">
          Reciprocal Match Discovery
        </h1>

        <p className="text-sm text-[#5C627A] max-w-md mx-auto mb-8 leading-relaxed">
          Reciprocal compatibility ranking combining interview preferences, scenario alignment, and multi-dimensional scoring into transparent, top-ranked candidate recommendations.
        </p>

        <div className="p-4 bg-[#FAF6F0] rounded-xl border border-[#E8E3DC] text-xs text-[#5C627A] flex items-center gap-3 mb-8 text-left">
          <Clock className="w-5 h-5 text-[#E07A5F] shrink-0" />
          <span>
            Reciprocal ranker endpoint (<code className="bg-white px-1 py-0.5 rounded border border-[#E8E3DC] text-[#2B2D42]">GET /api/v1/matches/:id</code>) is ready in the backend engine.
          </span>
        </div>

        <Link to="/">
          <Button variant="secondary" icon={ArrowRight}>
            Back to Welcome Page
          </Button>
        </Link>
      </Card>
    </div>
  );
};

export default MatchesPlaceholder;
