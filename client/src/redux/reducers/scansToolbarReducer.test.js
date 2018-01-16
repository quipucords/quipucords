import scansToolbarReducer from './scansToolbarReducer';

describe('scansToolbarReducer', function() {
  it('should return the initial state', () => {
    const initialState = {
      filterType: null,
      filterValue: '',
      activeFilters: [],
      sortType: null,
      sortAscending: true
    };

    expect(scansToolbarReducer(undefined, {})).toEqual(initialState);
  });
});
