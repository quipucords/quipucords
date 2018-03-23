import expect from 'expect';
import { reducers } from '../../reducers';

describe('FactsActions', function() {
  it('Get the initial state', () => {
    expect(reducers.facts.initialState).toBeDefined();
  });
});
