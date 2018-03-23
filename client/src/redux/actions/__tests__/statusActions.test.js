import expect from 'expect';
import { reducers } from '../../reducers';

describe('StatusActions', function() {
  it('Get the initial state', () => {
    expect(reducers.status.initialState).toBeDefined();
  });
});
