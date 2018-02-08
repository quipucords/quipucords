import toolbarsReducer from './toolbarsReducer';

describe('toolbarsReducer', function() {
  it('should return the initial state', () => {
    const initialState = {
      SOURCES_VIEW: {
        filterType: null,
        filterValue: '',
        activeFilters: [],
        sortType: null,
        sortAscending: true
      },
      SCANS_VIEW: {
        filterType: null,
        filterValue: '',
        activeFilters: [],
        sortType: null,
        sortAscending: true
      },
      CREDENTIALS_VIEW: {
        filterType: null,
        filterValue: '',
        activeFilters: [],
        sortType: null,
        sortAscending: true
      }
    };

    expect(toolbarsReducer(undefined, {})).toEqual(initialState);
  });
});
