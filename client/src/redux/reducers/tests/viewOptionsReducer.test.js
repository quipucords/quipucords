import viewOptionsReducer from '../viewOptionsReducer';

describe('viewOptionsReducer', function() {
  it('should return the initial state', () => {
    const initialState = {
      SOURCES_VIEW: {
        currentPage: 1,
        pageSize: 15,
        totalCount: 0,
        totalPages: 0,
        filterType: null,
        filterValue: '',
        activeFilters: [],
        sortType: null,
        sortField: 'name',
        sortAscending: true
      },
      SCANS_VIEW: {
        currentPage: 1,
        pageSize: 15,
        totalCount: 0,
        totalPages: 0,
        filterType: null,
        filterValue: '',
        activeFilters: [],
        sortType: null,
        sortField: 'name',
        sortAscending: true
      },
      CREDENTIALS_VIEW: {
        currentPage: 1,
        pageSize: 15,
        totalCount: 0,
        totalPages: 0,
        filterType: null,
        filterValue: '',
        activeFilters: [],
        sortType: null,
        sortField: 'name',
        sortAscending: true
      }
    };

    expect(viewOptionsReducer(undefined, {})).toEqual(initialState);
  });
});
