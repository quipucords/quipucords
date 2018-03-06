import _ from 'lodash';
import helpers from '../../common/helpers';
import { sourcesTypes } from '../constants';

const initialState = {
  persist: {
    selectedSources: []
  },

  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    sources: []
  },

  update: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    sourceId: '',
    delete: false
  }
};

const selectedIndex = function(state, source) {
  return _.findIndex(state.persist.selectedSources, nextSelected => {
    return nextSelected.id === _.get(source, 'id');
  });
};

const sourcesReducer = function(state = initialState, action) {
  switch (action.type) {
    // Persist
    case sourcesTypes.SELECT_SOURCE:
      // Do nothing if it is already selected
      if (selectedIndex(state, action.source) !== -1) {
        return state;
      }

      return helpers.setStateProp(
        'persist',
        {
          selectedSources: [...state.persist.selectedSources, action.source]
        },
        {
          state,
          reset: false
        }
      );

    case sourcesTypes.DESELECT_SOURCE:
      const index = selectedIndex(state, action.source);

      // Do nothing if it is not already selected
      if (index === -1) {
        return state;
      }

      return helpers.setStateProp(
        'persist',
        {
          selectedSources: [
            ...state.persist.selectedSources.slice(0, index),
            ...state.persist.selectedSources.slice(index + 1)
          ]
        },
        {
          state,
          reset: false
        }
      );

    // Error/Rejected
    case sourcesTypes.DELETE_SOURCE_REJECTED:
    case sourcesTypes.DELETE_SOURCES_REJECTED:
      return helpers.setStateProp(
        'update',
        {
          error: action.error,
          errorMessage: _.get(action.payload, 'response.data.detail', action.payload.message),
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case sourcesTypes.DELETE_SOURCE_PENDING:
    case sourcesTypes.DELETE_SOURCES_PENDING:
      return helpers.setStateProp(
        'update',
        {
          pending: true,
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case sourcesTypes.DELETE_SOURCE_FULFILLED:
    case sourcesTypes.DELETE_SOURCES_FULFILLED:
      return helpers.setStateProp(
        'update',
        {
          fulfilled: true,
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case sourcesTypes.GET_SOURCES_REJECTED:
      return helpers.setStateProp(
        'view',
        {
          error: action.error,
          errorMessage: _.get(action.payload, 'response.data.detail', action.payload.message)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case sourcesTypes.GET_SOURCES_PENDING:
      return helpers.setStateProp(
        'view',
        {
          pending: true,
          sources: state.view.sources
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case sourcesTypes.GET_SOURCES_FULFILLED:
      // Get resulting credentials and update the selected state of each
      const sources = _.get(action, 'payload.data.results', []).map(nextSource => {
        return {
          ...nextSource,
          selected: selectedIndex(state, nextSource) !== -1
        };
      });
      return helpers.setStateProp(
        'view',
        {
          sources: sources,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    default:
      return state;
  }
};

export { initialState, sourcesReducer };

export default sourcesReducer;
