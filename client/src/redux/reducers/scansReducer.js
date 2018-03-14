import helpers from '../../common/helpers';
import { scansTypes } from '../constants';

const initialState = {
  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    scans: []
  },

  detail: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    scan: {}
  },

  results: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    results: []
  },

  jobs: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    jobs: []
  },

  action: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    add: false,
    start: false,
    cancel: false,
    pause: false,
    restart: false
  },

  update: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    delete: false
  }
};

const scansReducer = function(state = initialState, action) {
  switch (action.type) {
    // Error/Rejected
    case helpers.rejectedAction(scansTypes.GET_SCANS):
      return helpers.setStateProp(
        'view',
        {
          pending: false,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.pendingAction(scansTypes.GET_SCANS):
      return helpers.setStateProp(
        'view',
        {
          pending: true,
          scans: state.view.scans
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.fulfilledAction(scansTypes.GET_SCANS):
      return helpers.setStateProp(
        'view',
        {
          scans: action.payload.data.results,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case helpers.rejectedAction(scansTypes.GET_SCAN):
      return helpers.setStateProp(
        'detail',
        {
          pending: false,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.pendingAction(scansTypes.GET_SCAN):
      return helpers.setStateProp(
        'detail',
        {
          pending: true,
          scan: state.detail.scans
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.fulfilledAction(scansTypes.GET_SCAN):
      return helpers.setStateProp(
        'detail',
        {
          scan: action.payload.data.results,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case helpers.rejectedAction(scansTypes.GET_SCAN_RESULTS):
      return helpers.setStateProp(
        'results',
        {
          pending: false,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.pendingAction(scansTypes.GET_SCAN_RESULTS):
      return helpers.setStateProp(
        'results',
        {
          pending: true,
          results: state.results.results
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.fulfilledAction(scansTypes.GET_SCAN_RESULTS):
      return helpers.setStateProp(
        'results',
        {
          results: action.payload.data.results,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case helpers.rejectedAction(scansTypes.GET_SCAN_JOBS):
      return helpers.setStateProp(
        'jobs',
        {
          pending: false,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.pendingAction(scansTypes.GET_SCAN_JOBS):
      return helpers.setStateProp(
        'jobs',
        {
          pending: true,
          jobs: state.jobs.jobs
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.fulfilledAction(scansTypes.GET_SCAN_JOBS):
      return helpers.setStateProp(
        'jobs',
        {
          jobs: action.payload.data.results,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case helpers.rejectedAction(scansTypes.ADD_SCAN):
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          add: true,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.pendingAction(scansTypes.ADD_SCAN):
      return helpers.setStateProp(
        'action',
        {
          add: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.fulfilledAction(scansTypes.ADD_SCAN):
      return helpers.setStateProp(
        'action',
        {
          add: true,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    case scansTypes.RESET_SCAN_ADD_STATUS:
      return helpers.setStateProp(
        'action',
        {
          error: false,
          errorMessage: '',
          fulfilled: false
        },
        {
          state,
          reset: false
        }
      );

    // Error/Rejected
    case helpers.rejectedAction(scansTypes.START_SCAN):
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          start: true,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.pendingAction(scansTypes.START_SCAN):
      return helpers.setStateProp(
        'action',
        {
          start: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.fulfilledAction(scansTypes.START_SCAN):
      return helpers.setStateProp(
        'action',
        {
          start: true,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case helpers.rejectedAction(scansTypes.CANCEL_SCAN):
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          cancel: true,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.pendingAction(scansTypes.CANCEL_SCAN):
      return helpers.setStateProp(
        'action',
        {
          cancel: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.fulfilledAction(scansTypes.CANCEL_SCAN):
      return helpers.setStateProp(
        'action',
        {
          cancel: true,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case helpers.rejectedAction(scansTypes.PAUSE_SCAN):
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          pause: true,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.pendingAction(scansTypes.PAUSE_SCAN):
      return helpers.setStateProp(
        'action',
        {
          pause: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.fulfilledAction(scansTypes.PAUSE_SCAN):
      return helpers.setStateProp(
        'action',
        {
          pause: true,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case helpers.rejectedAction(scansTypes.RESTART_SCAN):
      return helpers.setStateProp(
        'action',
        {
          pending: false,
          restart: true,
          error: action.error,
          errorMessage: helpers.getErrorMessageFromResults(action.payload)
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case helpers.pendingAction(scansTypes.RESTART_SCAN):
      return helpers.setStateProp(
        'action',
        {
          restart: true,
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case helpers.fulfilledAction(scansTypes.RESTART_SCAN):
      return helpers.setStateProp(
        'action',
        {
          restart: true,
          pending: false,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case helpers.rejectedAction(scansTypes.DELETE_SCAN):
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

    case helpers.pendingAction(scansTypes.DELETE_SCAN):
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

    case helpers.fulfilledAction(scansTypes.DELETE_SCAN):
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

    default:
      return state;
  }
};

export { initialState, scansReducer };

export default scansReducer;
