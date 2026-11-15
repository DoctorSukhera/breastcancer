import unittest
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; GEN=ROOT/'results'/'generated'

class TestIntegrityCheckpointInvariants(unittest.TestCase):
    def test_reference_counts(self):
        ref=pd.read_csv(ROOT/'data/frozen/reference_policy.csv')
        self.assertEqual(len(ref),760)
        self.assertEqual(ref.reference_outcome.value_counts().to_dict(),{'COMPLETE':629,'FAIL_SAFE':71,'BLOCK':60})

    def test_primary_controller_values(self):
        d=pd.read_csv(GEN/'benchmark_controller_summary.csv').set_index('system')
        expected={'Static workflow':0.3684210526,'Goal planner':0.5578947368,'Adaptive planner':0.7157894737,'Bounded controller':1.0}
        for k,v in expected.items(): self.assertAlmostEqual(float(d.loc[k,'policy_conformance']),v,9)
        self.assertAlmostEqual(float(d.loc['Static workflow','action_appropriateness']),0.2092105263,9)
        self.assertAlmostEqual(float(d.loc['Goal planner','action_appropriateness']),0.6828947368,9)
        self.assertAlmostEqual(float(d.loc['Adaptive planner','action_appropriateness']),0.6828947368,9)
        b=d.loc['Bounded controller']
        for col in ['feasible_goal_completion','action_appropriateness','safety_conformance','provenance_conformance','escalation_conformance','resource_stewardship']:
            self.assertAlmostEqual(float(b[col]),1.0,9)
        self.assertAlmostEqual(float(b.mean_oracle_cost),4.8289473684,9)
        self.assertAlmostEqual(float(b.mean_cost),4.8289473684,9)
        self.assertAlmostEqual(float(b.mean_actions),7.0276315789,9)

    def test_deterministic_values(self):
        d=pd.read_csv(GEN/'deterministic_error_handling_summary.csv').iloc[0]
        self.assertAlmostEqual(float(d.policy_conformance),1.0,9)
        self.assertAlmostEqual(float(d.action_appropriateness),0.8421052632,9)
        self.assertAlmostEqual(float(d.resource_stewardship),0.9926196881,9)
        self.assertAlmostEqual(float(d.mean_oracle_cost),4.8289473684,9)
        self.assertAlmostEqual(float(d.mean_cost),4.8684210526,9)
        self.assertAlmostEqual(float(d.mean_actions),7.0276315789,9)

    def test_ablation_values(self):
        d=pd.read_csv(GEN/'ablation_summary_metrics.csv').set_index('system')
        self.assertAlmostEqual(float(d.loc['Replanning removed','policy_conformance']),0.9210526316,9)
        self.assertAlmostEqual(float(d.loc['Replanning removed','transient_recovery_rate']),0.5,9)
        self.assertAlmostEqual(float(d.loc['Verifier removed','policy_conformance']),0.9078947368,9)
        self.assertAlmostEqual(float(d.loc['Safety gate removed','policy_conformance']),0.9210526316,9)
        self.assertAlmostEqual(float(d.loc['Safety gate removed','resource_stewardship']),0.9210526316,9)
        self.assertAlmostEqual(float(d.loc['Provenance removed','policy_conformance']),0.9342105263,9)
        self.assertAlmostEqual(float(d.loc['Cost-awareness removed','policy_conformance']),1.0,9)
        self.assertAlmostEqual(float(d.loc['Verifier removed','action_appropriateness']),0.9539473684,9)
        self.assertAlmostEqual(float(d.loc['Verifier removed','resource_stewardship']),0.9634549008390542,9)
        self.assertAlmostEqual(float(d.loc['Cost-awareness removed','resource_stewardship']),0.9959253432494279,9)

    def test_transient_cost_alignment(self):
        d=pd.read_csv(GEN/'benchmark_trajectory_level.csv')
        t=d[(d.system=='Bounded controller') & (d.family=='transient_failure')]
        self.assertEqual(len(t),120)
        self.assertAlmostEqual(float((t.actual_cost-t.oracle_cost).abs().max()),0.0,12)

if __name__=='__main__': unittest.main(verbosity=2)
