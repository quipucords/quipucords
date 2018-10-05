import helpers from '../../../common/helpers';
import { scansTypes } from '../../constants/index';
import scansReducer from '../scansReducer';

const initialState = {
  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    scans: [],
    sourcesCount: 0
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

  merge_dialog: {
    show: false,
    scans: [],
    details: false
  }
};

describe('scansReducer', () => {
  it('should return the initial state', () => {
    expect(scansReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle GET_SCANS_REJECTED', () => {
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.GET_SCANS)
    };

    const resultState = scansReducer(undefined, dispatched);

    expect(resultState.view.pending).toBeTruthy();

    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
  });

  it('should handle GET_SCANS_FULFILLED', () => {
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.GET_SCAN)
    };

    const resultState = scansReducer(undefined, dispatched);

    expect(resultState.detail.pending).toBeTruthy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.jobs).toEqual(initialState.jobs);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
  });

  it('should handle GET_SCAN_FULFILLED', () => {
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.GET_SCAN_JOBS)
    };

    const resultState = scansReducer(undefined, dispatched);

    expect(resultState.jobs.pending).toBeTruthy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.detail).toEqual(initialState.detail);
  });

  it('should handle GET_SCAN_JOBS_FULFILLED', () => {
    const mockResults = [
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

    const dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.GET_SCAN_JOBS),
      payload: {
        data: {
          results: mockResults
        }
      }
    };

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.GET_SCAN_CONNECTION_RESULTS)
    };

    const resultState = scansReducer(undefined, dispatched);

    expect(resultState.connectionResults.pending).toBeTruthy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.inspectionResults).toEqual(initialState.inspectionResults);
    expect(resultState.jobs).toEqual(initialState.jobs);
  });

  it('should handle GET_SCAN_CONNECTION_RESULTS_FULFILLED', () => {
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.GET_SCAN_INSPECTION_RESULTS)
    };

    const resultState = scansReducer(undefined, dispatched);

    expect(resultState.inspectionResults.pending).toBeTruthy();

    expect(resultState.view).toEqual(initialState.view);
    expect(resultState.action).toEqual(initialState.action);
    expect(resultState.update).toEqual(initialState.update);
    expect(resultState.detail).toEqual(initialState.detail);
    expect(resultState.connectionResults).toEqual(initialState.connectionResults);
    expect(resultState.jobs).toEqual(initialState.jobs);
  });

  it('should handle GET_SCAN_INSPECTION_RESULTS_FULFILLED', () => {
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.ADD_SCAN)
    };

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.ADD_SCAN),
      payload: {}
    };

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.START_SCAN)
    };

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.START_SCAN),
      payload: {}
    };

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.CANCEL_SCAN)
    };

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.CANCEL_SCAN),
      payload: {}
    };

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.PAUSE_SCAN)
    };

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.PAUSE_SCAN),
      payload: {}
    };

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.RESTART_SCAN)
    };

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.RESTART_SCAN),
      payload: {}
    };

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
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

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.PENDING_ACTION(scansTypes.DELETE_SCAN)
    };

    const resultState = scansReducer(undefined, dispatched);

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
    const dispatched = {
      type: helpers.FULFILLED_ACTION(scansTypes.DELETE_SCAN),
      payload: {}
    };

    const resultState = scansReducer(undefined, dispatched);

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
});
