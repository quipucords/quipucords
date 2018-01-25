import credentialsToolbarReducer from './credentialsToolbarReducer';

describe('credentialsToolbarReducer', function() {
  it('should return the initial state', () => {
    const initialState = {
      filterType: null,
      filterValue: '',
      activeFilters: [],
      sortType: null,
      sortAscending: true
    };

    expect(credentialsToolbarReducer(undefined, {})).toEqual(initialState);
  });
});
