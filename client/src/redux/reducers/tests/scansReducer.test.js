import helpers from '../../../common/helpers';
import { scansTypes } from '../../constants/index';
import scansReducer from '../scansReducer';

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

  connectionResults: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    results: []
  },

  inspectionResults: {
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
  },

  merge: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false
  },

  merge_dialog: {
    show: false,
    scans: [],
    details: false
  }
};

describe('scansReducer', function() {
  it('should return the initial state', () => {
    expect(scansReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle GET_SCANS_REJECTED', () => {
    let dispatched = {
      type: helpers.REJECTED_ACTION(scansTypes.GET_SCANS),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'GET ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.view.error).toBeTruthy();
    expect(resultState.view.errorMessage).toEqual('GET ERROR');

    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
  });

  it('should handle GET_SCANS_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.GET_SCANS)
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.view.pending).toBeTruthy();

    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
  });

  it('should handle GET_SCANS_FULFILLED', () => {
    let dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.GET_SCANS),
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

    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
  });

  it('should handle GET_SCAN_REJECTED', () => {
    let dispatched = {
      type: helpers.REJECTED_ACTION(scansTypes.GET_SCAN),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'GET ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.detail.error).toBeTruthy();
    expect(resultState.detail.errorMessage).toEqual('GET ERROR');

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
  });

  it('should handle GET_SCAN_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.GET_SCAN)
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.detail.pending).toBeTruthy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
  });

  it('should handle GET_SCAN_FULFILLED', () => {
    let dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.GET_SCAN),
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

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
  });

  it('should handle GET_SCAN_JOBS_REJECTED', () => {
    let dispatched = {
      type: helpers.REJECTED_ACTION(scansTypes.GET_SCAN_JOBS),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'GET JOBS ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.jobs.error).toBeTruthy();
    expect(resultState.jobs.errorMessage).toEqual('GET JOBS ERROR');

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle GET_SCAN_JOBS_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.GET_SCAN_JOBS)
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.jobs.pending).toBeTruthy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle GET_SCAN_JOBS_FULFILLED', () => {
    let mockResults = [
      {
        scan_type: 'inspect',
        options: {
          max_concurrency: 0,
          disabled_optional_products: {
            jboss_eap: true,
            jboss_fuse: true,
            jboss_brms: true
          }
        },
        id: 0,
        status: 'created',
        sources: [
          {
            id: 0,
            name: 'string',
            source_type: 'network'
          }
        ],
        tasks: [
          {
            source: 0,
            scan_type: 'inspect',
            status: 'created',
            start_time: '2018-02-23T20:37:42.989Z',
            end_time: '2018-02-23T20:37:42.989Z',
            systems_count: 0,
            systems_scanned: 0,
            systems_failed: 0
          }
        ],
        start_time: '2018-02-23T20:37:42.989Z',
        end_time: '2018-02-23T20:37:42.989Z',
        systems_count: 0,
        systems_scanned: 0,
        systems_failed: 0,
        report_id: 0
      }
    ];

    let dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.GET_SCAN_JOBS),
      payload: {
        data: {
          results: mockResults
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.jobs.fulfilled).toBeTruthy();
    expect(resultState.jobs.jobs).toEqual(mockResults);

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle GET_SCAN_CONNECTION_RESULTS_REJECTED', () => {
    let dispatched = {
      type: helpers.REJECTED_ACTION(scansTypes.GET_SCAN_CONNECTION_RESULTS),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'GET CONNECTION RESULTS ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.connectionResults.error).toBeTruthy();
    expect(resultState.connectionResults.errorMessage).toEqual('GET CONNECTION RESULTS ERROR');

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.jobs).toEqual(initialState.jobs);
  });

  it('should handle GET_SCAN_CONNECTION_RESULTS_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.GET_SCAN_CONNECTION_RESULTS)
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.connectionResults.pending).toBeTruthy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.jobs).toEqual(initialState.jobs);
  });

  it('should handle GET_SCAN_CONNECTION_RESULTS_FULFILLED', () => {
    let dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.GET_SCAN_CONNECTION_RESULTS),
      payload: {
        data: {
          results: [
            {
              name: '10.10.181.47',
              source: {
                id: 1,
                name: 'source 1',
                source_type: 'network'
              },
              status: 'success'
            },
            {
              name: '10.10.181.48',
              source: {
                id: 1,
                name: 'source 1',
                source_type: 'network'
              },
              status: 'success'
            },
            {
              name: '10.11.181.47',
              source: {
                id: 2,
                name: 'source 2',
                source_type: 'network'
              },
              status: 'success'
            },
            {
              name: '10.11.181.48',
              source: {
                id: 2,
                name: 'source 2',
                source_type: 'network'
              },
              status: 'success'
            }
          ]
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.connectionResults.fulfilled).toBeTruthy();
    expect(resultState.connectionResults.results).toHaveLength(4);

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.jobs).toEqual(initialState.jobs);
  });

  it('should handle GET_SCAN_INSPECTION_RESULTS_REJECTED', () => {
    let dispatched = {
      type: helpers.REJECTED_ACTION(scansTypes.GET_SCAN_INSPECTION_RESULTS),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'GET INSPECTION RESULTS ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.inspectionResults.error).toBeTruthy();
    expect(resultState.inspectionResults.errorMessage).toEqual('GET INSPECTION RESULTS ERROR');

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.jobs).toEqual(initialState.jobs);
  });

  it('should handle GET_SCAN_INSPECTION_RESULTS_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.GET_SCAN_INSPECTION_RESULTS)
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.inspectionResults.pending).toBeTruthy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.jobs).toEqual(initialState.jobs);
  });

  it('should handle GET_SCAN_INSPECTION_RESULTS_FULFILLED', () => {
    let dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.GET_SCAN_INSPECTION_RESULTS),
      payload: {
        data: {
          results: [
            {
              name: '10.10.181.47',
              source: {
                id: 1,
                name: 'source 1',
                source_type: 'network'
              },
              status: 'success'
            },
            {
              name: '10.10.181.48',
              source: {
                id: 1,
                name: 'source 1',
                source_type: 'network'
              },
              status: 'success'
            },
            {
              name: '10.11.181.47',
              source: {
                id: 2,
                name: 'source 2',
                source_type: 'network'
              },
              status: 'success'
            },
            {
              name: '10.11.181.48',
              source: {
                id: 2,
                name: 'source 2',
                source_type: 'network'
              },
              status: 'success'
            }
          ]
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.inspectionResults.fulfilled).toBeTruthy();
    expect(resultState.inspectionResults.results).toHaveLength(4);

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.jobs).toEqual(initialState.jobs);
  });

  it('should handle ADD_SCAN_REJECTED', () => {
    let dispatched = {
      type: helpers.REJECTED_ACTION(scansTypes.ADD_SCAN),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'ADD ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.error).toBeTruthy();
    expect(resultState.action.errorMessage).toEqual('ADD ERROR');
    expect(resultState.action.add).toBeTruthy();
    expect(resultState.action.start).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle ADD_SCAN_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.ADD_SCAN)
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.pending).toBeTruthy();
    expect(resultState.action.add).toBeTruthy();
    expect(resultState.action.start).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle ADD_SCAN_FULFILLED', () => {
    let dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.ADD_SCAN),
      payload: {}
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.fulfilled).toBeTruthy();
    expect(resultState.action.add).toBeTruthy();
    expect(resultState.action.start).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle START_SCAN_REJECTED', () => {
    let dispatched = {
      type: helpers.REJECTED_ACTION(scansTypes.START_SCAN),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'START ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.error).toBeTruthy();
    expect(resultState.action.errorMessage).toEqual('START ERROR');
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.start).toBeTruthy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle START_SCAN_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.START_SCAN)
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.pending).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.start).toBeTruthy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle START_SCAN_FULFILLED', () => {
    let dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.START_SCAN),
      payload: {}
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.fulfilled).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.start).toBeTruthy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle CANCEL_SCAN_REJECTED', () => {
    let dispatched = {
      type: helpers.REJECTED_ACTION(scansTypes.CANCEL_SCAN),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'CANCEL ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.error).toBeTruthy();
    expect(resultState.action.errorMessage).toEqual('CANCEL ERROR');
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.start).toBeFalsy();
    expect(resultState.action.cancel).toBeTruthy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle CANCEL_SCAN_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.CANCEL_SCAN)
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.pending).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.start).toBeFalsy();
    expect(resultState.action.cancel).toBeTruthy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle CANCEL_SCAN_FULFILLED', () => {
    let dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.CANCEL_SCAN),
      payload: {}
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.fulfilled).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.start).toBeFalsy();
    expect(resultState.action.cancel).toBeTruthy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle PAUSE_SCAN_REJECTED', () => {
    let dispatched = {
      type: helpers.REJECTED_ACTION(scansTypes.PAUSE_SCAN),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'PAUSE ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.error).toBeTruthy();
    expect(resultState.action.errorMessage).toEqual('PAUSE ERROR');
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.start).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeTruthy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle PAUSE_SCAN_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.PAUSE_SCAN)
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.pending).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.start).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeTruthy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle PAUSE_SCAN_FULFILLED', () => {
    let dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.PAUSE_SCAN),
      payload: {}
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.fulfilled).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.start).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeTruthy();
    expect(resultState.action.restart).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle RESTART_SCAN_REJECTED', () => {
    let dispatched = {
      type: helpers.REJECTED_ACTION(scansTypes.RESTART_SCAN),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'RESTART ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.error).toBeTruthy();
    expect(resultState.action.errorMessage).toEqual('RESTART ERROR');
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.start).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeTruthy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle RESTART_SCAN_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.RESTART_SCAN)
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.pending).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.start).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeTruthy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle RESTART_SCAN_FULFILLED', () => {
    let dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.RESTART_SCAN),
      payload: {}
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.action.fulfilled).toBeTruthy();
    expect(resultState.action.add).toBeFalsy();
    expect(resultState.action.start).toBeFalsy();
    expect(resultState.action.cancel).toBeFalsy();
    expect(resultState.action.pause).toBeFalsy();
    expect(resultState.action.restart).toBeTruthy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle DELETE_SCAN_REJECTED', () => {
    let dispatched = {
      type: helpers.REJECTED_ACTION(scansTypes.DELETE_SCAN),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'DELETE ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.update.delete).toBeTruthy();
    expect(resultState.update.error).toBeTruthy();
    expect(resultState.update.errorMessage).toEqual('DELETE ERROR');
    expect(resultState.update.fulfilled).toBeFalsy();
    expect(resultState.update.pending).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle DELETE_SCAN_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.DELETE_SCAN)
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.update.delete).toBeTruthy();
    expect(resultState.update.error).toBeFalsy();
    expect(resultState.update.errorMessage).toEqual('');
    expect(resultState.update.fulfilled).toBeFalsy();
    expect(resultState.update.pending).toBeTruthy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle DELETE_SCAN_FULFILLED', () => {
    let dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.DELETE_SCAN),
      payload: {}
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.update.delete).toBeTruthy();
    expect(resultState.update.error).toBeFalsy();
    expect(resultState.update.errorMessage).toEqual('');
    expect(resultState.update.fulfilled).toBeTruthy();
    expect(resultState.update.pending).toBeFalsy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle GET_MERGE_SCAN_RESULTS_REJECTED', () => {
    let dispatched = {
      type: helpers.REJECTED_ACTION(scansTypes.GET_MERGE_SCAN_RESULTS),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'MERGE ERROR'
          }
        }
      }
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.merge.error).toBeTruthy();
    expect(resultState.merge.errorMessage).toEqual('MERGE ERROR');
    expect(resultState.merge.pending).toBeFalsy();
    expect(resultState.merge.fulfilled).toBeFalsy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.deployments).toEqual(initialState.deployments);
    expect(resultState.details).toEqual(initialState.details);
  });

  it('should handle GET_MERGE_SCAN_RESULTS_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.GET_MERGE_SCAN_RESULTS)
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.merge.error).toBeFalsy();
    expect(resultState.merge.errorMessage).toEqual('');
    expect(resultState.merge.pending).toBeTruthy();
    expect(resultState.merge.fulfilled).toBeFalsy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.deployments).toEqual(initialState.deployments);
    expect(resultState.details).toEqual(initialState.details);
  });

  it('should handle GET_MERGE_SCAN_RESULTS_FULFILLED', () => {
    let dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.GET_MERGE_SCAN_RESULTS)
    };

    let resultState = scansReducer(undefined, dispatched);

    expect(resultState.merge.error).toBeFalsy();
    expect(resultState.merge.errorMessage).toEqual('');
    expect(resultState.merge.pending).toBeFalsy();
    expect(resultState.merge.fulfilled).toBeTruthy();

    expect(resultState.persist).toEqual(initialState.persist);
    expect(resultState.deployments).toEqual(initialState.deployments);
    expect(resultState.details).toEqual(initialState.details);
  });
});
