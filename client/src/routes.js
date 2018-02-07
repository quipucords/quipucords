import Scans from './components/scans/scans';
import Sources from './components/sources/sources';
import Credentials from './components/credentials/credentials';

const baseName = '/client';

/**
 * Return array of objects that describe vertical menu
 * @return {array}
 */
const routes = () => [
  {
    iconClass: 'pficon pficon-network',
    title: 'Sources',
    to: '/sources',
    redirect: true,
    component: Sources
  },
  {
    iconClass: 'fa fa-wifi',
    title: 'Scans',
    to: '/scans',
    component: Scans
  },
  {
    iconClass: 'fa fa-key',
    title: 'Credentials',
    to: '/credentials',
    component: Credentials
  }
];

export { baseName, routes };
