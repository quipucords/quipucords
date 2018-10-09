import viewOptionsReducer from '../viewOptionsReducer';

describe('viewOptionsReducer', () => {
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
        sortAscending: true,
        selectedItems: [],
        expandedItems: []
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
        sortAscending: true,
        selectedItems: [],
        expandedItems: []
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
        sortAscending: true,
        selectedItems: [],
        expandedItems: []
      }
    };

    expect(viewOptionsReducer(undefined, {})).toEqual(initialState);
  });
});
