"""Reproducible synthetic holdout evaluation; no real trial performance claim."""
from datetime import date, timedelta
import json
import math
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from study_operations import _forecast


def poisson(rng, rate):
    # Small synthetic daily rates; Knuth sampling needs no numerical dependency.
    count, product, cutoff = 0, 1.0, math.exp(-rate)
    while product > cutoff:
        product *= rng.random()
        count += 1
    return count - 1


def evaluate():
    rng = random.Random(26047)
    cutoff = date(2026, 9, 1)
    results = {}
    for scenario, multiplier in [('constant_rate', 1.0), ('unseen_50_percent_slowdown', .5)]:
        scores=[]
        for trial in range(150):
            rate = rng.uniform(.2, 2.4)
            observed = [poisson(rng, rate) for _ in range(56)]
            future = sum(poisson(rng, rate*multiplier) for _ in range(28))
            participants = [{'study_id':'SIM','enrolled_at':(cutoff-timedelta(days=55-day)).isoformat()}
                            for day, count in enumerate(observed) for _ in range(count)]
            remaining = max(1, round(28*rate*rng.uniform(.5, 1.5)))
            study = {'id':'SIM','start':(cutoff-timedelta(days=55)).isoformat(),
                     'end':(cutoff+timedelta(days=28)).isoformat(),'target':sum(observed)+remaining}
            forecast = _forecast(study, participants, cutoff)
            probability = forecast['target_probability_raw']
            lower, upper = forecast['predictive_enrolments_90']
            outcome = int(future >= remaining)
            posterior_mean = (.5+sum(observed))/56.5*28
            trailing_mean = sum(observed)/56*28
            scores.append({'brier':(probability-outcome)**2, 'model_mae':abs(posterior_mean-future),
                           'trailing_mae':abs(trailing_mean-future), 'covered':lower<=future<=upper})
        results[scenario] = {'studies':len(scores), **{
            name:round(sum(row[key] for row in scores)/len(scores),4)
            for name,key in [('target_probability_brier_score','brier'),('future_count_mae','model_mae'),
                             ('trailing_rate_count_mae','trailing_mae'),('nominal_90_percent_interval_coverage','covered')]}}
    return {'seed':26047,'observed_days':56,'holdout_days':28,'synthetic_studies':300,
            'method':'Study-level Gamma(0.5, rate 0.5 days) prior + Poisson likelihood; negative-binomial posterior prediction',
            'data_separation':'Only dates at or before the cutoff enter the forecast; holdout counts are used only for scoring.',
            'scenarios':results,
            'prior_review':'An initial diagnostic with seed 26046 showed excessive shrinkage from the Gamma(1,14) prior. This independent seed evaluates the revised weaker prior; the initial result is retained in forecast-prior-diagnostic.json.',
            'limitations':'Simulation checks method behaviour, not clinical validity. Stationarity violations can degrade forecasts; no superiority claim.'}


if __name__ == '__main__':
    result=evaluate()
    destination=ROOT/'docs/validation/forecast-evaluation.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
