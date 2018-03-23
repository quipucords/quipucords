import expect from 'expect';
import { reducers } from '../../reducers';

describe('ReportsActions', function() {
  it('Get the initial state', () => {
    expect(reducers.reports.initialState).toBeDefined();
  });
});
