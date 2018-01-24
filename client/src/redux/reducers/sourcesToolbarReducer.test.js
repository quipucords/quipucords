import sourcesToolbarReducer from './sourcesToolbarReducer';

describe('sourcesToolbarReducer', function() {
  it('should return the initial state', () => {
    const initialState = {
      filterType: null,
      filterValue: '',
      activeFilters: [],
      sortType: null,
      sortAscending: true
    };

    expect(sourcesToolbarReducer(undefined, {})).toEqual(initialState);
  });
});
