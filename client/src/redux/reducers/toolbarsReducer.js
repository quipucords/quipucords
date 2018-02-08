import { viewTypes, viewToolbarTypes } from '../constants';

let initialState = {};

initialState[viewTypes.SOURCES_VIEW] = {
  filterType: null,
  filterValue: '',
  activeFilters: [],
  sortType: null,
  sortAscending: true
};
initialState[viewTypes.SCANS_VIEW] = {
  filterType: null,
  filterValue: '',
  activeFilters: [],
  sortType: null,
  sortAscending: true
};
initialState[viewTypes.CREDENTIALS_VIEW] = {
  filterType: null,
  filterValue: '',
  activeFilters: [],
  sortType: null,
  sortAscending: true
};

export default function toolbarsReducer(state = initialState, action) {
  let updateState = {};

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
        activeFilters: [...state[action.viewType].activeFilters, action.filter]
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
            ]
          }
        );
        return Object.assign({}, state, updateState);
      } else {
        return state;
      }

    case viewToolbarTypes.CLEAR_FILTERS:
      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        activeFilters: []
      });
      return Object.assign({}, state, updateState);

    case viewToolbarTypes.SET_SORT_TYPE:
      if (state[action.viewType].sortType === action.sortType) {
        return state;
      }

      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        sortType: action.sortType,
        sortAscending: true
      });
      return Object.assign({}, state, updateState);

    case viewToolbarTypes.TOGGLE_SORT_ASCENDING:
      updateState[action.viewType] = Object.assign({}, state[action.viewType], {
        sortAscending: !state[action.viewType].sortAscending
      });
      return Object.assign({}, state, updateState);

    default:
      return state;
  }
}
