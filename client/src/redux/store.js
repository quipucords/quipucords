import { createStore, applyMiddleware } from 'redux';
import thunkMiddleware from 'redux-thunk';
import { createLogger } from 'redux-logger';
import promiseMiddleware from 'redux-promise-middleware';
import reduxReducers from './reducers';
import cookies from 'js-cookie';

const hydrateStore = () => {
  // Create any initial state items based on stored data (cookies etc.)
  return {};
};

let middleware = [thunkMiddleware, promiseMiddleware()];

if (process.env.NODE_ENV !== 'production') {
  if (process.env.REACT_APP_DEBUG_MIDDLEWARE === 'true') {
    middleware.push(createLogger());
  }
  cookies.set(
    'csrftoken',
    'xLPbEvorrDHqC9poUjUpKtJcf2kmskkwVzHpkiwqO57zD9ViBtrtqEud6llTnVPH'
  );
  console.warn('Warning: Loading spoof auth token.');
}

const store = createStore(
  reduxReducers,
  hydrateStore(),
  applyMiddleware(...middleware)
);

export default store;
