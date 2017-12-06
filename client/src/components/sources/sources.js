import PropTypes from 'prop-types';
import React from 'react';

const Sources = ({ children }) => (
  <div className="row">
    <div className='col-sm-12 main-content'>
      <span> Sources </span>
      {children}
    </div>
  </div>
);
Sources.propTypes = {
  children: PropTypes.node
};

export default Sources;
