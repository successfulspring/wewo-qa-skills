"""A human's overall confirmation plus explicit later business answers."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / p) for p in ('tooling/runtime','skills/wewo-qa-case-designer/scripts','skills/wewo-qa-case-executor/scripts','tests')]
from artifact_tools import load_json
from design_context import requirement_digest
from requirement_readiness import readiness_errors
from requirement_confirmation import business_snapshot


class RequirementConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.c = load_json(ROOT / 'tests/fixtures/design-context.json')

    def add_answer(self):
        c = self.c
        c['dialogue_events'] += [
            {'id':'EVT-Q2.1','kind':'question','message_ref':'synthetic://details/question',
             'text':'[SYNTHETIC] Does the scope remain the previously specified login flow?', 'question_ids':['Q2.1']},
            {'id':'EVT-A-DETAIL','kind':'answer','message_ref':'synthetic://details/answer',
             'text':'[SYNTHETIC] Yes, the same scope.', 'question_ids':['Q2.1'],'in_reply_to':'EVT-Q2.1'}]
        decision = {'id':'DEC-002','unit_id':'RU-001','question_id':'Q2.1','topic':'Scope restatement',
                    'resolution':'The same scope.', 'status':'confirmed','response_event_ref':'EVT-A-DETAIL'}
        c['decisions'].append(decision)
        c['branch_reviews'].append({'answer_event_ref':'EVT-A-DETAIL','unit_refs':['RU-001'],
                                   'note':'Synthetic restatement preserves behavior; no new obligations.'})
        c['requirement_items'].append({'id':'REQ2.1','origin_ref':'DEC-002','start':0,'end':len(decision['resolution']),
                                      'statement':decision['resolution'],'disposition':'context','rule_refs':[],
                                      'reason':'Restates the already confirmed scope.'})

    def test_later_answer_without_business_change_does_not_need_another_summary(self):
        original = copy.deepcopy(self.c['requirement_confirmation'])
        self.add_answer()
        self.c['requirement_review']['snapshot_sha256'] = requirement_digest(self.c)
        self.assertEqual(readiness_errors(self.c, confirmed=True), [])
        self.assertEqual(self.c['requirement_confirmation'], original)

    def test_silent_business_change_still_requires_authoritative_resolution(self):
        self.c['rules'][0]['expected'] = 'An invented different result'
        self.c['requirement_review']['snapshot_sha256'] = requirement_digest(self.c)
        self.assertTrue(readiness_errors(self.c, confirmed=True))

    def test_draft_confirmation_still_requires_complete_source_accounting(self):
        self.c['requirement_items'].pop(0)
        self.assertTrue(any('unaccounted source content' in e for e in readiness_errors(self.c, confirmed=True, final=False)))

    def test_draft_cannot_use_a_stale_confirmed_answer_after_a_followup(self):
        question = self.c['dialogue_events'][0]
        self.c['dialogue_events'].append({**question, 'id':'EVT-FOLLOWUP', 'message_ref':'synthetic://followup',
            'revisits':{qid:question['id'] for qid in question['question_ids']}})
        self.assertTrue(any('latest answer' in e for e in readiness_errors(self.c, confirmed=True, final=False)))

    def changed_rule(self):
        c = self.c
        c['requirement_confirmation']['baseline'] = business_snapshot(c)
        self.add_answer()
        rule = c['rules'][0]
        rule['expected'] = 'Home shows the account identifier'
        rule['decision_refs'].append('DEC-002')
        rule['requirement_refs'].append('REQ2.1')
        decision = c['decisions'][-1]
        decision.update(topic='Displayed identity', resolution='Home shows the account identifier')
        c['dialogue_events'][-1]['text'] = '[SYNTHETIC] Display the account identifier.'
        c['requirement_items'][-1].update(statement=decision['resolution'], end=len(decision['resolution']), disposition='requirement', rule_refs=[rule['id']])
        c['requirement_items'][-1].pop('reason')
        c['requirement_confirmation']['amendments'] = [{'ref':rule['id'], 'sha256':business_snapshot(c)[rule['id']], 'decision_refs':['DEC-002']}]
        c['requirement_review']['snapshot_sha256'] = requirement_digest(c)

    def test_scoped_answer_updates_rule_without_rewriting_original_confirmation(self):
        original = self.c['requirement_confirmation']['snapshot_sha256']
        self.changed_rule()
        self.assertEqual(readiness_errors(self.c, confirmed=True), [])
        self.assertEqual(self.c['requirement_confirmation']['snapshot_sha256'], original)

    def test_scoped_answer_does_not_approve_an_unrelated_rule_change(self):
        self.changed_rule()
        self.c['rules'][1]['expected'] = 'Invented lockout duration'
        self.c['requirement_review']['snapshot_sha256'] = requirement_digest(self.c)
        self.assertTrue(any('scoped confirmed amendment' in e for e in readiness_errors(self.c, confirmed=True)))

    def test_amendment_cannot_use_an_answer_from_another_unit(self):
        self.changed_rule()
        self.c['requirement_confirmation']['amendments'][0]['decision_refs'] = ['DEC-001']
        self.assertTrue(any('does not support this rule' in e for e in readiness_errors(self.c, confirmed=True)))

    def test_one_actual_reply_can_confirm_understanding_and_answer_questions(self):
        c = self.c
        c['dialogue_events'] = [e for e in c['dialogue_events'] if e['kind'] != 'answer']
        reply = c['dialogue_events'][-1]
        reply.update(answer_to=['EVT-QUESTION-001'], question_ids=['Q-RU002-01'], text='[SYNTHETIC] Overall scope confirmed; option B.')
        c['decisions'][0]['response_event_ref'] = reply['id']
        c['branch_reviews'][0]['answer_event_ref'] = reply['id']
        c['requirement_confirmation']['response_text'] = reply['text']
        self.assertEqual(readiness_errors(c, confirmed=True), [])


if __name__ == '__main__':
    unittest.main()
