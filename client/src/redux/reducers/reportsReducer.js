import helpers from '../../common/helpers';
import { reportsTypes } from '../constants';

const initialState = {
  report: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    reports: []
  },

  merge: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false
  }
};

const reportsReducer = (state = initialState, action) => {
  switch (action.type) {
    case helpers.REJECTED_ACTION(reportsTypes.GET_REPORT):
      return helpers.setStateProp(
        'report',
        {
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload).message
        },
        {
          state,
          initialState
        }
      );

    case helpers.REJECTED_ACTION(reportsTypes.GET_MERGE_REPORT):
      return helpers.setStateProp(
        'merge',
        {
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload).message
        },
        {
          state,
          initialState
        }
      );

    case helpers.PENDING_ACTION(reportsTypes.GET_REPORT):
      return helpers.setStateProp(
        'report',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.PENDING_ACTION(reportsTypes.GET_MERGE_REPORT):
      return helpers.setStateProp(
        'merge',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.FULFILLED_ACTION(reportsTypes.GET_REPORT):
      return helpers.setStateProp(
        'report',
        {
          fulfilled: true,
          reports: action.payload.data
        },
        {
          state,
          initialState
        }
      );

    case helpers.FULFILLED_ACTION(reportsTypes.GET_MERGE_REPORT):
      return helpers.setStateProp(
        'merge',
        {
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

reportsReducer.initialState = initialState;

export { reportsReducer as default, initialState, reportsReducer };
