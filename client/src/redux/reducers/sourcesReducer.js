import _ from 'lodash';
import helpers from '../../common/helpers';
import { sourcesTypes } from '../constants';

const initialState = {
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

const sourcesReducer = function(state = initialState, action) {
  switch (action.type) {
    // Error/Rejected
    case helpers.REJECTED_ACTION(sourcesTypes.DELETE_SOURCE):
    case helpers.REJECTED_ACTION(sourcesTypes.DELETE_SOURCES):
      return helpers.setStateProp(
        'update',
        {
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload),
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.PENDING_ACTION(sourcesTypes.DELETE_SOURCE):
    case helpers.PENDING_ACTION(sourcesTypes.DELETE_SOURCES):
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

    case helpers.FULFILLED_ACTION(sourcesTypes.DELETE_SOURCE):
    case helpers.FULFILLED_ACTION(sourcesTypes.DELETE_SOURCES):
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

    case helpers.REJECTED_ACTION(sourcesTypes.GET_SOURCES):
      return helpers.setStateProp(
        'view',
        {
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.PENDING_ACTION(sourcesTypes.GET_SOURCES):
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
    case helpers.FULFILLED_ACTION(sourcesTypes.GET_SOURCES):
      // Get resulting sources and update the selected state of each
      const sources = _.get(action, 'payload.data.results', []);
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

sourcesReducer.initialState = initialState;

export { initialState, sourcesReducer };

export default sourcesReducer;
