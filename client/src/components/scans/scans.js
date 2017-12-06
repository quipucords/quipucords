import PropTypes from 'prop-types';
import React from 'react';

const Scans = ({ children }) => (
  <div className="row">
    <div className='col-sm-12 main-content'>
      <span> Scans </span>
      {children}
    </div>
  </div>
);
Scans.propTypes = {
  children: PropTypes.node
};

export default Scans;
