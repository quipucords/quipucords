import expect from 'expect';
import moxios from 'moxios';
import promiseMiddleware from 'redux-promise-middleware';
import { createStore, applyMiddleware, combineReducers } from 'redux';
import { actions } from '../';
import { reducers } from '../../reducers';

describe('ScansActions', function() {
  const middleware = [promiseMiddleware()];
  const generateStore = () => createStore(combineReducers({ scans: reducers.scans }), applyMiddleware(...middleware));

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

  it('Update the scans view state when getScans is complete', done => {
    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      request.respondWith({
        status: 200,
        response: getScansMock
      });
    });

    const store = generateStore();
    expect(reducers.scans.initialState).toBeDefined();

    const dispatcher = actions.scans.getScans();
    dispatcher(store.dispatch).then(() => {
      const view = store.getState().scans.view;

      expect(view.scans).toEqual(getScansMock.results);
      expect(view.fulfilled).toBeTruthy();
      expect(view.pending).toBeFalsy();
      expect(view.error).toBeFalsy();
      expect(view.errorMessage).toEqual('');

      done();
    });
  });
});
