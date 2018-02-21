import { scansTypes } from '../../constants/index';
import scansReducer from '../scansReducer';

const initialState = {
  persist: {},

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

  action: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    add: false,
    cancel: false,
    pause: false,
    restart: false
  }
};

describe('scansReducer', function() {
  it('should return the initial state', () => {
    expect(scansReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle GET_SCANS_REJECTED', () => {
    let dispatched = {
      type: scansTypes.GET_SCANS_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          request: {
            responseText: 'GET ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.view.error).toBeTruthy();
    expect(resultState.view.errorMessage).toEqual('GET ERROR');

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.results).toEqual(initialState.results);
  });

  it('should handle GET_SCANS_PENDING', () => {
    let dispatched = {
      type: scansTypes.GET_SCANS_PENDING
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.view.pending).toBeTruthy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.results).toEqual(initialState.results);
  });

  it('should handle GET_SCANS_FULFILLED', () => {
    let dispatched = {
      type: scansTypes.GET_SCANS_FULFILLED,
      payload: {
        data: {
          results: [
            {
              name: '1',
              id: 1
            },
            {
              name: '2',
              id: 2
            },
            {
              name: '3',
              id: 3
            },
            {
              name: '4',
              id: 4
            }
          ]
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.view.fulfilled).toBeTruthy();
    expect(resultState.view.scans).toHaveLength(4);

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.results).toEqual(initialState.results);
  });

  it('should handle GET_SCAN_REJECTED', () => {
    let dispatched = {
      type: scansTypes.GET_SCAN_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          request: {
            responseText: 'GET ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.detail.error).toBeTruthy();
    expect(resultState.detail.errorMessage).toEqual('GET ERROR');

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.results).toEqual(initialState.results);
  });

  it('should handle GET_SCAN_PENDING', () => {
    let dispatched = {
      type: scansTypes.GET_SCAN_PENDING
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.detail.pending).toBeTruthy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.results).toEqual(initialState.results);
  });

  it('should handle GET_SCAN_FULFILLED', () => {
    let dispatched = {
      type: scansTypes.GET_SCAN_FULFILLED,
      payload: {
        data: {
          results: {
            name: '1',
            id: 1
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.detail.fulfilled).toBeTruthy();
    expect(resultState.detail.scan.id).toEqual(1);

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.results).toEqual(initialState.results);
  });

  it('should handle GET_SCAN_RESULTS_REJECTED', () => {
    let dispatched = {
      type: scansTypes.GET_SCAN_RESULTS_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          request: {
            responseText: 'GET RESULTS ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.results.error).toBeTruthy();
    expect(resultState.results.errorMessage).toEqual('GET RESULTS ERROR');

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle GET_SCAN_RESULTS_PENDING', () => {
    let dispatched = {
      type: scansTypes.GET_SCAN_RESULTS_PENDING
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.results.pending).toBeTruthy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle GET_SCAN_RESULTS_FULFILLED', () => {
    let dispatched = {
      type: scansTypes.GET_SCAN_RESULTS_FULFILLED,
      payload: {
        data: {
          results: {
            connection_results: [
              {
                task_results: [
                  {
                    source: {
                      id: 0,
                      name: 'task result 0',
                      source_type: 'network'
                    },
                    systems: [
                      {
                        name: '0',
                        credential: {
                          id: 0,
                          name: 'credential 0',
                          cred_type: 'network'
                        },
                        status: 'success'
                      }
                    ]
                  }
                ]
              }
            ],
            inspection_results: [
              {
                task_results: [
                  {
                    source: {
                      id: 0,
                      name: 'source 0',
                      source_type: 'network'
                    },
                    systems: [
                      {
                        name: '0',
                        facts: [
                          {
                            name: 'fact 0',
                            value: 'value 0'
                          }
                        ],
                        status: 'success'
                      }
                    ]
                  }
                ]
              }
            ]
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.results.fulfilled).toBeTruthy();
    expect(resultState.results.results.connection_results[0].task_results[0].source.id).toEqual(0);

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle ADD_SCAN_REJECTED', () => {
    let dispatched = {
      type: scansTypes.ADD_SCAN_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          request: {
            responseText: 'ADD ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.error).toBeTruthy();
    expect(resultState.action.errorMessage).toEqual('ADD ERROR');
    expect(resultState.action.add).toBeTruthy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.results).toEqual(initialState.results);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle ADD_SCAN_PENDING', () => {
    let dispatched = {
      type: scansTypes.ADD_SCAN_PENDING
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.pending).toBeTruthy();
    expect(resultState.action.add).toBeTruthy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.results).toEqual(initialState.results);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle ADD_SCAN_FULFILLED', () => {
    let dispatched = {
      type: scansTypes.ADD_SCAN_FULFILLED,
      payload: {}
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.fulfilled).toBeTruthy();
    expect(resultState.action.add).toBeTruthy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.results).toEqual(initialState.results);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle CANCEL_SCAN_REJECTED', () => {
    let dispatched = {
      type: scansTypes.CANCEL_SCAN_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          request: {
            responseText: 'CANCEL ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.error).toBeTruthy();
    expect(resultState.action.errorMessage).toEqual('CANCEL ERROR');
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.cancel).toBeTruthy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.results).toEqual(initialState.results);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle CANCEL_SCAN_PENDING', () => {
    let dispatched = {
      type: scansTypes.CANCEL_SCAN_PENDING
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.pending).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.cancel).toBeTruthy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.results).toEqual(initialState.results);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle CANCEL_SCAN_FULFILLED', () => {
    let dispatched = {
      type: scansTypes.CANCEL_SCAN_FULFILLED,
      payload: {}
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.fulfilled).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.cancel).toBeTruthy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.results).toEqual(initialState.results);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle PAUSE_SCAN_REJECTED', () => {
    let dispatched = {
      type: scansTypes.PAUSE_SCAN_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          request: {
            responseText: 'PAUSE ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.error).toBeTruthy();
    expect(resultState.action.errorMessage).toEqual('PAUSE ERROR');
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeTruthy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.results).toEqual(initialState.results);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle PAUSE_SCAN_PENDING', () => {
    let dispatched = {
      type: scansTypes.PAUSE_SCAN_PENDING
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.pending).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeTruthy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.results).toEqual(initialState.results);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle PAUSE_SCAN_FULFILLED', () => {
    let dispatched = {
      type: scansTypes.PAUSE_SCAN_FULFILLED,
      payload: {}
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.fulfilled).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeTruthy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.results).toEqual(initialState.results);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle RESTART_SCAN_REJECTED', () => {
    let dispatched = {
      type: scansTypes.RESTART_SCAN_REJECTED,
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          request: {
            responseText: 'RESTART ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.error).toBeTruthy();
    expect(resultState.action.errorMessage).toEqual('RESTART ERROR');
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeTruthy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.results).toEqual(initialState.results);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle RESTART_SCAN_PENDING', () => {
    let dispatched = {
      type: scansTypes.RESTART_SCAN_PENDING
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.pending).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeTruthy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.results).toEqual(initialState.results);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle RESTART_SCAN_FULFILLED', () => {
    let dispatched = {
      type: scansTypes.RESTART_SCAN_FULFILLED,
      payload: {}
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.fulfilled).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeTruthy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.results).toEqual(initialState.results);
    expect(resultState.detail).toEqual(initialState.detail);
  });
});
