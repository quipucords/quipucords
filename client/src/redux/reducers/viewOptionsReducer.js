import {
  viewTypes,
  viewPaginationTypes,
  viewToolbarTypes,
  credentialsTypes,
  scansTypes,
  sourcesTypes
} from '../constants';

let initialState = {};

initialState[viewTypes.SOURCES_VIEW] = {
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
};
initialState[viewTypes.SCANS_VIEW] = {
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
};
initialState[viewTypes.CREDENTIALS_VIEW] = {
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
};

export default function toolbarsReducer(state = initialState, action) {
  let updateState = {};

  let updatePageCounts = (viewType, itemsCount) => {
    let totalCount = itemsCount;

    // TODO: Remove this when we get decent data back in development mode
    if (process.env.NODE_ENV === 'development') {
      totalCount = Math.abs(itemsCount) % 1000;
    }

    let totalPages = Math.ceil(totalCount / state[viewType].pageSize);

    updateState[viewType] = Object.assign({}, state[viewType], {
      totalCount: totalCount,
      totalPages: totalPages,
      currentPage: Math.min(state[viewType].currentPage, totalPages || 1)
    });
  };

  switch (action.type) {
    case viewToolbarTypes.SET_FILTER_TYPE:
      if (state[action.viewType].filterType === action.filterType) {
        return state;
      }

      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        filterType: action.filterType,
        filterValue: ''
      });
      return Object.assign({}, state, updateState);

    case viewToolbarTypes.SET_FILTER_VALUE:
      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        filterValue: action.filterValue
      });
      return Object.assign({}, state, updateState);

    case viewToolbarTypes.ADD_FILTER:
      // Don't rea-add the same filter
      let filterExists = state[action.viewType].activeFilters.find(filter => {
        return (
          action.filter.field === filter.field &&
          action.filter.value === filter.value
        );
      });
      if (filterExists) {
        return state;
      }

      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        activeFilters: [...state[action.viewType].activeFilters, action.filter],
        currentPage: 1
      });
      return Object.assign({}, state, updateState);

    case viewToolbarTypes.REMOVE_FILTER:
      let index = state[action.viewType].activeFilters.indexOf(action.filter);
      if (index >= 0) {
        updateState[action.viewType] = Object.assign(
          {},
          state[action.viewType],
          {
            activeFilters: [
              ...state[action.viewType].activeFilters.slice(0, index),
              ...state[action.viewType].activeFilters.slice(index + 1)
            ],
            currentPage: 1
          }
        );
        return Object.assign({}, state, updateState);
      } else {
        return state;
      }

    case viewToolbarTypes.CLEAR_FILTERS:
      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        activeFilters: [],
        currentPage: 1
      });
      return Object.assign({}, state, updateState);

    case viewToolbarTypes.SET_SORT_TYPE:
      if (state[action.viewType].sortType === action.sortType) {
        return state;
      }

      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        sortType: action.sortType,
        sortField: action.sortType.id,
        sortAscending: true,
        currentPage: 1
      });
      return Object.assign({}, state, updateState);

    case viewToolbarTypes.TOGGLE_SORT_ASCENDING:
      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        sortAscending: !state[action.viewType].sortAscending,
        currentPage: 1
      });
      return Object.assign({}, state, updateState);

    case viewPaginationTypes.VIEW_FIRST_PAGE:
      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        currentPage: 1
      });
      return Object.assign({}, state, updateState);

    case viewPaginationTypes.VIEW_LAST_PAGE:
      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        currentPage: state[action.viewType].totalPages
      });
      return Object.assign({}, state, updateState);

    case viewPaginationTypes.VIEW_PREVIOUS_PAGE:
      if (state[action.viewType].currentPage < 2) {
        return state;
      }

      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        currentPage: state[action.viewType].currentPage - 1
      });
      return Object.assign({}, state, updateState);

    case viewPaginationTypes.VIEW_NEXT_PAGE:
      if (
        state[action.viewType].currentPage >= state[action.viewType].totalPages
      ) {
        return state;
      }
      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        currentPage: state[action.viewType].currentPage + 1
      });
      return Object.assign({}, state, updateState);

    case viewPaginationTypes.VIEW_PAGE_NUMBER:
      if (
        !Number.isInteger(action.pageNumber) ||
        action.pageNumber < 1 ||
        action.pageNumber > state[action.viewType].totalPages
      ) {
        return state;
      }

      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        currentPage: action.pageNumber
      });
      return Object.assign({}, state, updateState);

    case viewPaginationTypes.SET_PER_PAGE:
      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        pageSize: action.pageSize
      });
      return Object.assign({}, state, updateState);

    case credentialsTypes.GET_CREDENTIAL_FULFILLED:
    case credentialsTypes.GET_CREDENTIALS_FULFILLED:
      updatePageCounts(viewTypes.CREDENTIALS_VIEW, action.payload.data.count);
      return Object.assign({}, state, updateState);

    case sourcesTypes.GET_SOURCE_FULFILLED:
    case sourcesTypes.GET_SOURCES_FULFILLED:
      updatePageCounts(viewTypes.SOURCES_VIEW, action.payload.data.count);
      return Object.assign({}, state, updateState);

    case scansTypes.GET_SCAN_FULFILLED:
    case scansTypes.GET_SCANS_FULFILLED:
      updatePageCounts(viewTypes.SCANS_VIEW, action.payload.data.count);
      return Object.assign({}, state, updateState);

    default:
      return state;
  }
}
