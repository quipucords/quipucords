import promiseMiddleware from 'redux-promise-middleware';
import { createStore, applyMiddleware, combineReducers } from 'redux';
import expect from 'expect';

import * as actions from '../scansActions';
import { reducers } from '../../reducers';

// const mockStore = configureMockStore(middlewares);

import moxios from 'moxios';
import scansReducer from '../../reducers/scansReducer';

describe('ScansActions', function() {
  const middlewares = [promiseMiddleware()];
  const generateStore = () => createStore(combineReducers({ ...reducers }), applyMiddleware(...middlewares));

  beforeEach(() => {
    moxios.install();
  });

  afterEach(() => {
    moxios.uninstall();
  });

  const getScansMock = {
    results: [
      {
        name: '1',
        id: 1
      },
      {
        name: '5',
        id: 5
      },
      {
        name: '6',
        id: 6
      },
      {
        name: '7',
        id: 7
      }
    ],
    headers: { 'content-type': 'application/json' }
  };

  it('updates the scans view state when getScans has been done', done => {
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      request.respondWith({
        status: 200,
        response: getScansMock
      });
    });

    const store = generateStore();
    expect(store.scans).toEqual(scansReducer.initialState);
    let dispatcher = actions.getScans();
    dispatcher(store.dispatch).then(() => {
      let view = store.getState().scans.view;
      expect(view.scans).toEqual(getScansMock.results);
      expect(view.fulfilled).toBeTruthy();
      expect(view.pending).toBeFalsy();
      expect(view.error).toBeFalsy();
      expect(view.errorMessage).toEqual('');
      done();
    });
  });
});
