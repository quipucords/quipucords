import { viewToolbarTypes } from '../constants';

const initialState = {
  filterType: null,
  filterValue: '',
  activeFilters: [],
  sortType: null,
  sortAscending: true
};

export default function scansToolbarReducer(state = initialState, action) {
  switch (action.type) {
    case viewToolbarTypes.SET_FILTER_TYPE:
      if (state.filterType === action.filterType) {
        return state;
      }
      return Object.assign({}, state, {
        filterType: action.filterType,
        filterValue: ''
      });

    case viewToolbarTypes.SET_FILTER_VALUE:
      return Object.assign({}, state, { filterValue: action.filterValue });

    case viewToolbarTypes.ADD_FILTER:
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

    case viewToolbarTypes.REMOVE_FILTER:
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

    case viewToolbarTypes.CLEAR_FILTERS:
      return Object.assign({}, state, { activeFilters: [] });

    case viewToolbarTypes.SET_SORT_TYPE:
      if (state.sortType === action.sortType) {
        return state;
      }

      return Object.assign({}, state, {
        sortType: action.sortType,
        sortAscending: true
      });

    case viewToolbarTypes.TOGGLE_SORT_ASCENDING:
      return Object.assign({}, state, {
        sortAscending: !state.sortAscending
      });

    default:
      return state;
  }
}
