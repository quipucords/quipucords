import { createStore, applyMiddleware } from 'redux';
import thunkMiddleware from 'redux-thunk';
import { createLogger } from 'redux-logger';
import promiseMiddleware from 'redux-promise-middleware';
import reduxReducers from './reducers';

// Create any initial state items based on stored data (cookies etc.)
const hydrateStore = () => {};

const middleware = [thunkMiddleware, promiseMiddleware()];

if (process.env.NODE_ENV !== 'production' && process.env.REACT_APP_DEBUG_MIDDLEWARE === 'true') {
  middleware.push(createLogger());
}

const store = createStore(reduxReducers, hydrateStore(), applyMiddleware(...middleware));

export default store;
