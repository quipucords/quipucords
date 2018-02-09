import helpers from '../../common/helpers';
import { scansTypes } from '../constants';

const initialState = {
  persist: {},

  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    scans: []
  }
};

const scansReducer = function(state = initialState, action) {
  switch (action.type) {
    // Error/Rejected
    case scansTypes.GET_SCANS_REJECTED:
      return helpers.setStateProp(
        'view',
        {
          error: action.payload.error,
          errorMessage: action.payload.message
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case scansTypes.GET_SCANS_PENDING:
      return helpers.setStateProp(
        'view',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case scansTypes.GET_SCANS_FULFILLED:
      return helpers.setStateProp(
        'view',
        {
          scans: action.payload,
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

export { initialState, scansReducer };

export default scansReducer;
