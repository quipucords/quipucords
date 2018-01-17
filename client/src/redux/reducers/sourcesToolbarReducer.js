import * as types from '../constants/viewToolbarConstants';

const initialState = {
  filterType: null,
  filterValue: '',
  activeFilters: [],
  sortType: null,
  sortAscending: true
};

export default function sourcesToolbarReducer(state = initialState, action) {
  switch (action.type) {
    case types.SET_FILTER_TYPE:
      if (state.filterType === action.filterType) {
        return state;
      }
      return Object.assign({}, state, {
        filterType: action.filterType,
        filterValue: ''
      });

    case types.SET_FILTER_VALUE:
      return Object.assign({}, state, { filterValue: action.filterValue });

    case types.ADD_FILTER:
      // Don't rea-add the same filter
      let filterExists = state.activeFilters.find(filter => {
        return (
          action.filter.field === filter.field &&
          action.filter.value === filter.value
        );
      });
      if (filterExists) {
        return state;
      }

      return Object.assign({}, state, {
        activeFilters: [...state.activeFilters, action.filter]
      });

    case types.REMOVE_FILTER:
      let index = state.activeFilters.indexOf(action.filter);
      if (index >= 0) {
        return Object.assign({}, state, {
          activeFilters: [
            ...state.activeFilters.slice(0, index),
            ...state.activeFilters.slice(index + 1)
          ]
        });
      } else {
        return state;
      }

    case types.CLEAR_FILTERS:
      return Object.assign({}, state, { activeFilters: [] });

    case types.SET_SORT_TYPE:
      if (state.sortType === action.sortType) {
        return state;
      }

      return Object.assign({}, state, {
        sortType: action.sortType,
        sortAscending: true
      });

    case types.TOGGLE_SORT_ASCENDING:
      return Object.assign({}, state, {
        sortAscending: !state.sortAscending
      });

    default:
      return state;
  }
}
