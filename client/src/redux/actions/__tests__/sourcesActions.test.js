import expect from 'expect';
import { reducers } from '../../reducers';

describe('SourcesActions', function() {
  it('Get the initial state', () => {
    expect(reducers.sources.initialState).toBeDefined();
  });
});
